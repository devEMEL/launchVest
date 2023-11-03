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
  const [appId, setAppId] = useState<number>(466175126)
  const [investType, setInvestType] = useState<number>(0)
  const [assetName, setAssetName] = useState<string>('')
  const [imageURL, setImageURL] = useState<string>('')
  const [project, setProject] = useState<object>({})

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
      id: 462048462,
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
          'owner address': String(tokenList[0]),
          'start timestamp': Number(tokenList[1]),
          'end timestamp': Number(tokenList[2]),
          'claim timestamp': Number(tokenList[3]),
          'asset id': Number(tokenList[4]),
          'asset decimal': Number(tokenList[5]),
          'image url': String(tokenList[6]),
          'asset price': Number(tokenList[7]),
          'min buy': Number(tokenList[8]),
          'max buy': Number(tokenList[9]),
          'max cap': Number(tokenList[10]),
          'assets for sale': Number(tokenList[11]),
          ispaused: tokenList[12],
          'initiated withdrawal': tokenList[13],
          'assets sold': Number(tokenList[14]),
          'amount raised': Number(tokenList[15]),
          'proceeds withdrawn': tokenList[16],
          'vesting schedule': Number(tokenList[17]),
        }
        projectObj = project
      }
    }

    return projectObj
  }
  const convertTimestampToDate = (timestamp: number) => {
    let dateFormat = new Date(timestamp * 1000)
    return ''.concat(dateFormat.getDate(), '/', dateFormat.getMonth() + 1, '/', dateFormat.getFullYear(), ' ')
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
    const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
      from: String(activeAddress),
      to: String(project['owner address']),
      amount: BigInt(6_000_000),
      suggestedParams: await algodClient.getTransactionParams().do(),
    })

    const isStaking = await checkIsStaking()

    const tx = await launchVestClient.invest(
      { is_staking: Boolean(isStaking), project: BigInt(project['asset id']), txn },
      {
        boxes: [algosdk.decodeAddress(activeAddress).publicKey, tokenKey],
      },
    )
    console.log(tx)
  }

  const claimTxn = async () => {
    const isStaking = await checkIsStaking()
    const tx = await launchVestClient.claimIdoAsset(
      { project: BigInt(project['asset id']), is_staking: Boolean(isStaking) },
      {
        boxes: [algosdk.decodeAddress(activeAddress).publicKey, tokenKey],
      },
    )
    console.log(tx)
    return tx
  }

  const reclaimTxn = async () => {
    const isStaking = await checkIsStaking()
    const tx = await launchVestClient.reclaimInvestment(
      { project: BigInt(project['asset id']), is_staking: Boolean(isStaking) },
      {
        boxes: [algosdk.decodeAddress(activeAddress).publicKey, tokenKey],
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
            <h1>{project['max cap']}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>amount raised</h1>
            <h1>${project['amount raised']}</h1>
          </div>
          <div className="capitalize p-2 flex justify-between">
            <h1>assets for sale</h1>
            <h1>{project['assets for sale']}</h1>
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
                dispatch(showConfirmModal())
                setInvestType(0)
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
          {investType == 0 && <ConfirmModal text="Buy" txn={buyTxnAction} />}

          {investType == 1 && <ConfirmModal text="Claim" txn={claimTxnAction} />}

          {investType == 2 && <ConfirmModal text="Reclaim" txn={reclaimTxnAction} />}
        </div>
      </div>
    </div>
  )
}

export default ProjectPage
