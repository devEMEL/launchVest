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

const QUATERLY = 7_884_000n
const HALF_A_YEAR = 15_768_000n
const YEARLY = 31_536_000n

const PER_BOX_MBR = 0.0025e6
const PER_BYTE_MBR = 0.0004e6

const ListToken = () => {
  const [appId, setAppId] = useState<number>(455380620)
  const [assetId, setAssetId] = useState<bigint>(0n)
  const [startTimestamp, setStartTimestamp] = useState<bigint>(0n)
  const [endTimestamp, setEndTimestamp] = useState<bigint>(0n)
  const [claimTimestamp, setClaimTimestamp] = useState<bigint>(0n)
  const [assetPrice, setAssetPrice] = useState<bigint>(0n)
  const [minimumBuy, setMinimumBuy] = useState<bigint>(0n)
  const [maximumBuy, setMaximumBuy] = useState<bigint>(0n)
  const [imageURL, setImageURL] = useState<string>('')
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
    await launchVestClient.bootstrap()
    console.log(launchVestAppId)
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!(assetId && startTimestamp && endTimestamp && claimTimestamp && assetPrice && minimumBuy && maximumBuy && imageURL)) return
    // const tokenKey = algosdk.bigIntToBytes(Number(assetId), 8)
    const tokenKey = algosdk.encodeUint64(BigInt(assetId))
    const tupleType = algosdk.ABIType.from('(uint64,uint64,uint64,uint64,uint64,uint64,uint64)')
    const encodedTuple = tupleType.encode([
      BigInt(assetId),
      BigInt(startTimestamp),
      BigInt(endTimestamp),
      BigInt(claimTimestamp),
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
        start_timestamp: BigInt(startTimestamp),
        end_timestamp: BigInt(endTimestamp),
        claim_timestamp: BigInt(claimTimestamp),
        price_per_asset: BigInt(assetPrice),
        max_investment_per_investor: BigInt(maximumBuy),
        min_investment_per_investor: BigInt(minimumBuy),
        
      },
      {
        boxes: [tokenKey],
        sendParams: { fee: algokit.microAlgos(200_000) },
      },
    )
    console.log(listToken)
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
            <label htmlFor="start__timestamp" className="text-2xl capitalize">
              Start Timestamp
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="start__timestamp"
                id="start__timestamp"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setStartTimestamp(e.target.value as unknown as bigint)
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
                type="text"
                name="end__timestamp"
                id="end__timestamp"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setEndTimestamp(e.target.value as unknown as bigint)
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
                type="text"
                name="claim__timestamp"
                id="claim__timestamp"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setClaimTimestamp(e.target.value as unknown as bigint)
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
              Minimum Buy
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
              Maximum Buy
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
            <label htmlFor="image_url" className="text-2xl capitalize">
              Image URL
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
            <button
              onClick={() => {
                setVestingSchedule(QUATERLY)
              }}
            >
              <div id="_3months" ref={_3months} className="bg-black text-[16px] text-white mr-20 py-5 px-20 hover:font-bold capitalize">
                3 months
              </div>
            </button>
            <button
              onClick={() => {
                setVestingSchedule(HALF_A_YEAR)
              }}
            >
              <div id="_6months" ref={_6months} className="bg-black text-[16px] text-white mr-20 py-5 px-20 hover:font-bold capitalize">
                6 months
              </div>
            </button>
            <button
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
            Submit
          </button>
        </form>
      </div>

      <button onClick={() => handleCreate()}>create app</button>
      <button onClick={() => handleShowProjects()}>showProjects</button>
    </div>
  )
}

export default ListToken
