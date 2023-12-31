import { FormEvent, useEffect, useState, useRef } from 'react'
import { LaunchVestClient } from '../contracts/launch_vest'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk'

// 444276289 - Tokenza
// 1698243333

// 1698275123
// 1698277123

const QUATERLY = 7_776_000n
const HALF_A_YEAR = 15_552_000n
const YEARLY = 31_536_000n

const PER_BOX_MBR = 0.0025e6
const PER_BYTE_MBR = 0.0004e6

const USDC_ASSET_ID = 10458941

const ListToken = () => {
  const [appId, setAppId] = useState<number>(479832604)
  const [amountOfAsset, setAmountOfAsset] = useState<bigint>(0n)
  const [assetId, setAssetId] = useState<bigint>(0n)
  const [startTimestamp, setStartTimestamp] = useState<string>('')
  const [endTimestamp, setEndTimestamp] = useState<string>('')
  const [claimTimestamp, setClaimTimestamp] = useState<string>('')
  const [assetPrice, setAssetPrice] = useState<bigint>(0n)
  const [minimumBuy, setMinimumBuy] = useState<bigint>(0n)
  const [maximumBuy, setMaximumBuy] = useState<bigint>(0n)
  const [imageURL, setImageURL] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)

  const [vestingSchedule, setVestingSchedule] = useState<bigint>(QUATERLY)

  const _3months = useRef()
  const _6months = useRef()
  const _1year = useRef()

  const { enqueueSnackbar } = useSnackbar()
  const { signer, activeAddress } = useWallet()
  const algodConfig = getAlgodConfigFromViteEnvironment()
  const algodClient = algokit.getAlgoClient({
    server: algodConfig.server,
    port: algodConfig.port,
    token: algodConfig.token,
  })

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const sender = { signer, addr: activeAddress! }

  const launchVestClient = new LaunchVestClient(
    {
      resolveBy: 'id',
      id: appId,
      sender,
    },
    algodClient,
  )
 
  const handleCreate = async () => {
    await launchVestClient.create.bare()
    const launchVestAppId = (await launchVestClient.appClient.getAppReference()).appId
    setAppId(Number(launchVestAppId))
    await launchVestClient.appClient.fundAppAccount(algokit.microAlgos(200_000))
    await launchVestClient.bootstrap({asset: USDC_ASSET_ID})
    console.log(launchVestAppId)
  }

  // const shortenURL = async (URL: string) => {
  //   let _result;
  //   await fetch('https://api-ssl.bitly.com/v4/shorten', {
  //     method: 'POST',
  //     mode: 'cors',
  //     headers: {
  //       Authorization: import.meta.env.VITE_APP_BITLY_TOKEN,
  //       'Content-Type': 'application/json',
  //     },
  //     body: JSON.stringify({
  //       long_url: imageURL,
  //       domain: 'bit.ly',
  //       group_guid: import.meta.env.VITE_APP_GUID,
  //     }),
  //   })
  //     .then((res) => res.json())
  //     .then(async(data) => {
  //       const new_link = data.link.replace('https://', '')
  //       await fetch(`https://api-ssl.bitly.com/v4/bitlinks/${new_link}/qr?image_format=png`, {
  //         mode: 'cors',
  //         headers: {
  //           Authorization: `Bearer ${import.meta.env.VITE_APP_BITLY_TOKEN}`,
  //         },
  //       })
  //         .then((res) => res.json())
  //         .then((result) => {
  //           _result = result
  //         })
  //     })
  //     return _result;
  // }

  const toTimestamp = (strDate: string) => {
    const dt = Date.parse(strDate)
    return dt / 1000
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)

    try {
      const _startTimestamp = toTimestamp(startTimestamp)
      const _endTimestamp = toTimestamp(endTimestamp)
      const _claimTimestamp = toTimestamp(claimTimestamp)

      if (!(assetId && startTimestamp && endTimestamp && claimTimestamp && assetPrice && minimumBuy && maximumBuy && imageURL)) {
        enqueueSnackbar(`Error: Make sure all fields are set.`, { variant: 'error' })
        return
      } else {
        // const tokenKey = algosdk.bigIntToBytes(Number(assetId), 8)
        const tokenKey = algosdk.encodeUint64(BigInt(assetId))
        const tupleType = algosdk.ABIType.from('(uint64,uint64,uint64,uint64,uint64,uint64,uint64)')
        const encodedTuple = tupleType.encode([
          BigInt(assetId),
          BigInt(_startTimestamp),
          BigInt(_endTimestamp),
          BigInt(_claimTimestamp),
          BigInt(assetPrice),
          BigInt(maximumBuy),
          BigInt(minimumBuy),
        ])
        const costTokenBox = PER_BOX_MBR + PER_BYTE_MBR * (8 + encodedTuple.byteLength * 2)
        console.log(costTokenBox)
        await launchVestClient.appClient.fundAppAccount(algokit.microAlgos(costTokenBox + 400_000))

        const listToken = await launchVestClient.listProject(
          {
            asset_id: BigInt(assetId),
            image_url: String(imageURL),
            start_timestamp: BigInt(_startTimestamp),
            end_timestamp: BigInt(_endTimestamp),
            claim_timestamp: BigInt(_claimTimestamp),
            price_per_asset: BigInt(assetPrice),
            max_investment_per_investor: BigInt(maximumBuy),
            min_investment_per_investor: BigInt(minimumBuy),
            vesting_schedule: BigInt(vestingSchedule),
          },
          {
            boxes: [tokenKey],
            sendParams: { fee: algokit.microAlgos(200_000) },
          },
        )

        const appAddress = (await launchVestClient.appClient.getAppReference()).appAddress

        const decimals = (await algodClient.getAssetByID(Number(assetId)).do()).params.decimals
        console.log(decimals);
        
        const _amountOfAsset = BigInt(amountOfAsset) * BigInt(10 ** decimals)
        console.log(_amountOfAsset);
        
        const txn = algosdk.makeAssetTransferTxnWithSuggestedParamsFromObject({
          from: String(activeAddress),
          to: appAddress,
          amount: BigInt(_amountOfAsset),
          assetIndex: Number(assetId),
          suggestedParams: await algodClient.getTransactionParams().do(),
        })
        await launchVestClient.depositIdoAssets(
          {txn: txn, asset: BigInt(assetId)},
          {
            boxes: [tokenKey],
          },
        )
        console.log(listToken)
        enqueueSnackbar(`Project Listed successfully`)
      }
    } catch (e) {
      enqueueSnackbar(`Error listing project: ${(e as Error).message}`, { variant: 'error' })
      setLoading(false)
      return
    }
  }
  return (
    <div className="max-w-[60%] w-[100%] mx-auto">
      <div className="capitalize text-4xl flex justify-center py-5">list token</div>
      <div className="border-2 border-black-100 rounded-[50px] p-10 mb-10">
        <form onSubmit={(e) => handleSubmit(e)}>
          <div className="mb-5">
            <label htmlFor="asset_id" className="text-2xl capitalize">
              Asset ID
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="asset_id"
                id="asset_id"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg"
                onChange={(e) => {
                  setAssetId(e.target.value as unknown as bigint)
                }}
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="amount_of_asset" className="text-2xl capitalize">
              Amount of asset
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="amount_of_asset"
                id="amount_of_asset"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setAmountOfAsset(e.target.value as unknown as bigint)
                }}
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="start__timestamp" className="text-2xl capitalize">
              Start Timestamp
            </label>
            <div className="mt-3">
              <input
                type="datetime-local"
                name="start__timestamp"
                id="start__timestamp"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setStartTimestamp(e.target.value as unknown as string)
                }}
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="end__timestamp" className="text-2xl capitalize">
              End Timestamp
            </label>
            <div className="mt-3">
              <input
                type="datetime-local"
                name="end__timestamp"
                id="end__timestamp"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setEndTimestamp(e.target.value as unknown as string)
                }}
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="claim__timestamp" className="text-2xl capitalize">
              Claim Timestamp
            </label>
            <div className="mt-3">
              <input
                type="datetime-local"
                name="claim__timestamp"
                id="claim__timestamp"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setClaimTimestamp(e.target.value as unknown as string)
                }}
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="asset__price" className="text-2xl capitalize">
              Asset Price ($)
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="asset__price"
                id="asset__price"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setAssetPrice(e.target.value as unknown as bigint)
                }}
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="minimum__buy" className="text-2xl capitalize">
              Minimum Buy ($)
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="minimum__buy"
                id="minimum__buy"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setMinimumBuy(e.target.value as unknown as bigint)
                }}
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="maximum__buy" className="text-2xl capitalize">
              Maximum Buy ($)
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="maximum__buy"
                id="maximum__buy"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setMaximumBuy(e.target.value as unknown as bigint)
                }}
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="image_url" className="text-2xl">
              Image URL{' '}
              <span className="text-[15px]">(ipfs/&#123;CID&#125; e.g ipfs://QmVoqUN21MPm91XffyBcVWQhemSLd1WjKY2a8Zr5WJDA9e)</span>
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="image_url"
                id="image_url"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setImageURL(e.target.value as unknown as string)
                }}
              />
            </div>
          </div>

          <div className="mt-10">
            <h1 className="text-2xl capitalize">Vesting schedule</h1>
          </div>

          <div
            onClick={(e) => {
              console.log(e.target.id)
              if (e.target.id === '_3months') {
                _3months.current.style.backgroundColor = '#FFFFFF'
                _3months.current.style.color = '#000000'
                _3months.current.style.border = '2px solid black'
                _6months.current.style.backgroundColor = 'black'
                _6months.current.style.color = '#FFFFFF'
                _1year.current.style.backgroundColor = 'black'
                _1year.current.style.color = '#FFFFFF'
              }
              if (e.target.id === '_6months') {
                _6months.current.style.backgroundColor = '#FFFFFF'
                _6months.current.style.color = '#000000'
                _6months.current.style.border = '2px solid black'
                _3months.current.style.backgroundColor = 'black'
                _3months.current.style.color = '#FFFFFF'
                _1year.current.style.backgroundColor = 'black'
                _1year.current.style.color = '#FFFFFF'
              }
              if (e.target.id === '_1year') {
                _1year.current.style.backgroundColor = '#FFFFFF'
                _1year.current.style.color = '#000000'
                _1year.current.style.border = '2px solid black'
                _6months.current.style.backgroundColor = 'black'
                _6months.current.style.color = '#FFFFFF'
                _3months.current.style.backgroundColor = 'black'
                _3months.current.style.color = '#FFFFFF'
              }
            }}
            className="flex justify-center items-center my-10 mx-auto"
          >
            <button type='button'
              onClick={() => {
                setVestingSchedule(QUATERLY)
              }}
            >
              <div id="_3months" ref={_3months} className="bg-black text-[16px] text-white mr-20 py-5 px-20 hover:font-bold capitalize">
                3 months
              </div>
            </button>
            <button type='button'
              onClick={() => {
                setVestingSchedule(HALF_A_YEAR)
              }}
            >
              <div id="_6months" ref={_6months} className="bg-black text-[16px] text-white mr-20 py-5 px-20 hover:font-bold capitalize">
                6 months
              </div>
            </button>
            <button type='button'
              onClick={() => {
                setVestingSchedule(YEARLY)
              }}
            >
              <div id="_1year" ref={_1year} className="bg-black text-[16px] text-white mr-20 py-5 px-20 hover:font-bold capitalize ">
                1 year
              </div>
            </button>
          </div>

          <button
            type="submit"
            className="w-[100%] h-[50px] border-2 outline-0 rounded-full bg-[#000000] text-[16px] text-[#ffffff] font-bold shadow-lg shadow-indigo-500/40"
          >
            {loading  ? <div className="loading loading-spinner" /> : 'submit'}
          </button>
        </form>
      </div>

      <button onClick={() => handleCreate()}>create app</button>
    </div>
  )
}

export default ListToken
