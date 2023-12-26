import { useEffect, useState } from 'react'
import { LaunchVestClient } from '../contracts/launch_vest'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk'
import Project from './Project'
import { useParams } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { showConfirmModal, hideConfirmModal } from '../services/features/confirmModal/confirmModalSlice'
import ConfirmModal from './Modals/ConfirmModal'
import { VestStakeClient } from '../contracts/vest_stake'

const ProjectPage = () => {
  const [appId, setAppId] = useState<number>(479832604)
  const [amount, setAmount] = useState<bigint>(0n)
  const [showModal, setShowModal] = useState<boolean>(false)
  const [investType, setInvestType] = useState<number>(0)
  const [assetName, setAssetName] = useState<string>('')
  const [imageURL, setImageURL] = useState<string>('')
  const [project, setProject] = useState<object>({})
  const [algoInUSD, setAlgoInUSD] = useState<number>(0)
  const { enqueueSnackbar } = useSnackbar()
  const { signer, activeAddress } = useWallet()
  const algodConfig = getAlgodConfigFromViteEnvironment()
  const algodClient = algokit.getAlgoClient({
    server: algodConfig.server,
    port: algodConfig.port,
    token: algodConfig.token,
  })
  const dispatch = useDispatch()
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const sender = { signer, addr: activeAddress! }
  const assetParams = useParams()

  const vestStakeClient = new VestStakeClient(
    {
      resolveBy: 'id',
      id: 479773538,
      sender,
    },
    algodClient,
  )
  const launchVestClient = new LaunchVestClient(
    {
      resolveBy: 'id',
      id: appId,
      sender,
    },
    algodClient,
  )

  const handleShowProjects = async () => {
    console.log(assetParams)
    let projectObj = {}
    for (let _box of await launchVestClient.appClient.getBoxNames()) {
      let result = await launchVestClient.appClient.getBoxValue(_box)

      const resultCodec = algosdk.ABIType.from(
        '(address,uint64,uint64,uint64,uint64,uint64,string,uint64,uint64,uint64,uint64,uint64,bool,bool,uint64,uint64,uint64,uint64)',
      )
      const tokenList = resultCodec.decode(result)
      console.log(tokenList)
      if (tokenList.length == 18 && tokenList[4] == assetParams.projectId) {
        let project = {
          'owner address': tokenList[0],
          'start timestamp': Number(tokenList[1]),
          'end timestamp': Number(tokenList[2]),
          'claim timestamp': Number(tokenList[3]),
          'asset id': Number(tokenList[4]),
          'asset decimal': Number(tokenList[5]),
          'image url': tokenList[6],
          'asset price': Number(tokenList[7]),
          'min buy': Number(tokenList[8]),
          'max buy': Number(tokenList[9]),
          'max cap': Number(tokenList[10]),
          'assets for sale': Number(tokenList[11]),
          ispaused: tokenList[12],
          'initiated withdrawal': tokenList[13],
          'assets sold': Number(tokenList[14]),
          'amount raised': Number(tokenList[15]),
          'proceeds withdrawn': Number(tokenList[16]),
          'vesting schedule': Number(tokenList[17]),
        }
        projectObj = project
      }
    }

    return projectObj
  }
  const convertTimestampToDate = (timestamp: number) => {
    let dateFormat = new Date(timestamp * 1000)
    return ''.concat(
      dateFormat.getDate(),
      '/',
      dateFormat.getMonth() + 1,
      '/',
      dateFormat.getFullYear(),
      ' ',
      dateFormat.getHours(),
      ":",
      dateFormat.getMinutes(),
      ":",
      dateFormat.getSeconds()
    )
  }
  const handleShowProjectsAction = async () => {
    await handleShowProjects().then(async (project) => {
      console.log(project)
      await getAsset(project['asset id'])
      setProject(project)
    })
  }

  const checkIsStaking = async () => {
    console.log(assetParams)
    let _isStaking = false
    for (let _box of await vestStakeClient.appClient.getBoxNames()) {
      let result = await vestStakeClient.appClient.getBoxValue(_box)

      const resultCodec = algosdk.ABIType.from('(address,uint64,uint64,bool,uint64,uint64)')
      const stakeList = resultCodec.decode(result)
      console.log(stakeList)
      if (stakeList.length == 6 && stakeList[0] == activeAddress && stakeList[3] == 1 && stakeList[2] == Number(assetParams)) {
        _isStaking = true
      }
    }

    return _isStaking
  }

  const getAssetImage = async (ipfsLink) => {
    const CID = ipfsLink.split('//')[1]
    return ''.concat(`https://ipfs.io/ipfs/${CID}`)
  }
  const getAssetImageAction = async () => {
    await getAssetImage(project['image url']).then((data) => {
      setImageURL(data)
    })
  }
  const getAsset = async (assetID: number) => {
    const asset = await algodClient.getAssetByID(assetID).do()
    setAssetName(asset.params.name)
  }
  useEffect(() => {
    handleShowProjectsAction()
    getAssetImageAction()
  }, [])

  const tokenKey = algosdk.encodeUint64(Number(assetParams.projectId))

  const buyTxn = async () => {
    const appAddress = (await launchVestClient.appClient.getAppReference()).appAddress
    let txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
      from: String(activeAddress),
      to: String(appAddress),
      // amount: BigInt(algosdk.algosToMicroalgos(Number(amount))),
      amount: BigInt(amount),
      suggestedParams: await algodClient.getTransactionParams().do(),
    })

    // const isStaking = await checkIsStaking()
    const isStaking = true
    console.log(isStaking)

    if (isStaking == true) {
      console.log('Staking')
    } else {
      console.log("Ain't staking bruh")
    }

    const amountInUSD = Math.trunc(Number(amount) * Number(algoInUSD))

    const allocation = Math.trunc((10 ** project['asset decimal'] * amountInUSD) / project['asset price'])
    console.log(amountInUSD)
    console.log(allocation)

    const tx = await launchVestClient.invest(
      {
        is_staking: Boolean(isStaking),
        project_id: BigInt(project['asset id']),
        amount_in_usd: BigInt(amountInUSD),
        txn,
        asset_allocation: BigInt(allocation),
      },
      {
        boxes: [tokenKey, algosdk.decodeAddress(activeAddress).publicKey],
      },
    )
    console.log(tx)
    // await handleShowProjectsAction()
  }

  const claimTxn = async () => {
    // const isStaking = await checkIsStaking()
    const isStaking = true
    const tx = await launchVestClient.claimIdoAsset(
      { project_id: BigInt(project['asset id']), is_staking: Boolean(isStaking) },
      {
        boxes: [tokenKey, algosdk.decodeAddress(activeAddress).publicKey],
      },
    )
    console.log(tx)
    return tx
  }

  const reclaimTxn = async () => {
    // const isStaking = await checkIsStaking()
    const isStaking = true
    const tx = await launchVestClient.reclaimInvestment(
      { project_id: BigInt(project['asset id']), is_staking: Boolean(isStaking) },
      {
        boxes: [tokenKey, algosdk.decodeAddress(activeAddress).publicKey],
      },
    )
    console.log(tx)
    return tx
  }

  const buyTxnAction = async () => {
    await buyTxn()
      .then(() => {
        enqueueSnackbar(`Presale purchase successfully.`, { variant: 'success' })
      })
      .catch((err) => {
        enqueueSnackbar(`presale purchase failed: ${(err as Error).message}`, { variant: 'error' })
      })
  }
  const claimTxnAction = async () => {
    await claimTxn()
      .then(() => {
        enqueueSnackbar(`Claimed successfully.`, { variant: 'success' })
      })
      .catch((err) => {
        enqueueSnackbar(`Claiming failed: ${(err as Error).message}`, { variant: 'error' })
      })
  }
  const reclaimTxnAction = async () => {
    await reclaimTxn()
      .then(() => {
        enqueueSnackbar(`Reclaimed successfully.`, { variant: 'success' })
      })
      .catch((err) => {
        enqueueSnackbar(`Reclaiming failed: ${(err as Error).message}`, { variant: 'error' })
      })
  }
  const truncateDecimal = (value, decimal) => {
    const str = String(value)
    let ans = str.substring(0, str.length - Number(decimal))
    return Number(ans)
  }

  return (
    <div className="max-w-[90%] w-[100%] m-auto">
      <div className="p-10 border-2 text-[20px] bg-black text-[#dddddd]">
        <h2 className="mb-2 text-center text-[25px]">{assetName}</h2>
        <div className="flex justify-center mt-5">
          <img src={imageURL} alt="" width={150} className="" />
        </div>
        <div className="">
          <div className="capitalize p-2 flex justify-between">
            <h1>asset id</h1>
            <h1>{project['asset id']}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>asset price</h1>
            <h1>{project['asset price']}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>start time</h1>
            <h1>{convertTimestampToDate(project['start timestamp'])}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>end time</h1>
            <h1>{convertTimestampToDate(project['end timestamp'])}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>claim time</h1>
            <h1>{convertTimestampToDate(project['claim timestamp'])}</h1>
          </div>

          <div className="capitalize p-2 flex justify-between">
            <h1>min buy</h1>
            <h1>{project['min buy']}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>max buy</h1>
            <h1>{project['max buy']}</h1>
          </div>

          <div className="capitalize p-2 flex justify-between">
            <h1>max cap</h1>
            <h1>{truncateDecimal(project['max cap'], project['asset decimal'])}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>amount raised</h1>
            <h1>${project['amount raised']}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>assets for sale</h1>
            <h1>{truncateDecimal(project['assets for sale'], project['asset decimal'])}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>assets sold</h1>
            <h1>{project['assets sold']}</h1>
          </div>
        </div>
        <div className="flex pt-10">
          <div className="basis-[50%] mr-5">
            <button
              className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full"
              onClick={() => {
                // dispatch(showConfirmModal())
                setShowModal(true)
                // setInvestType(0)
              }}
            >
              Buy
            </button>
          </div>
          <div className="basis-[50%] mr-5">
            <button
              className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full"
              onClick={() => {
                dispatch(showConfirmModal())
                setInvestType(1)
              }}
            >
              Claim
            </button>
          </div>
          <div className="basis-[50%]">
            <button
              className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full"
              onClick={() => {
                dispatch(showConfirmModal())
                setInvestType(2)
              }}
            >
              Reclaim
            </button>
          </div>

          {/* CONFIRM MODAL */}
          {showModal && (
            <div className="fixed w-full h-full top-[0] left-[0]">
              <div className="max-w-[400px] bg-gray-200 text-white p-10 w-full fixed top-[40%] left-[50%] -translate-x-[50%] -translate-y-[50%]">
                <div className="text-[20px] text-center font-bold">
                  {/* <select
                    name="currency"
                    id="currency"
                    className="bg-black mb-5 p-2"
                    onChange={(e) => {
                      console.log(e.target.value)
                      setCurrency(e.target.value)
                    }}
                  >
                    <option value="algo">ALGO</option>
                    <option value="usdc">USDC</option>
                  </select> */}
                  <input
                    type="text"
                    placeholder="Enter amount in Algo"
                    className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg text-black"
                    onChange={async (e) => {
                      setAmount(e.target.value as unknown as bigint)
                      await fetch('https://price-feeds.goracle.io/api/v2/crypto/prices?key=P6hT3kXpqbTNLWzyyyk1R7Crh&assets=algo&curr=usd')
                        .then((data) => data.json())
                        .then((result) => {
                          console.log(result[0].price)
                          let price = result[0].price
                          setAlgoInUSD(price)
                        })
                    }}
                  />
                </div>
                <div className="flex justify-between items-center mt-5">
                  <button className="p-3 border-2 bg-white text-black capitalize" onClick={() => setShowModal(false)}>
                    cancel
                  </button>
                  <button
                    className="p-3 border-2 bg-white text-black capitalize"
                    onClick={async () => {
                      // dispatch(hideConfirmModal())
                      // call function
                      // txn()
                      if (Number(amount) >= project['min buy'] && Number(amount) <= project['max buy']) {
                        await buyTxnAction()
                        console.log(amount)
                      } else {
                        enqueueSnackbar(`Invalid buy amount: `, { variant: 'error' })
                      }
                    }}
                  >
                    submit
                  </button>
                </div>
              </div>
            </div>
          )}

          {investType == 1 && <ConfirmModal text="Claim" txn={claimTxnAction} />}

          {investType == 2 && <ConfirmModal text="Reclaim" txn={reclaimTxnAction} />}
        </div>
      </div>
    </div>
  )
}

export default ProjectPage
