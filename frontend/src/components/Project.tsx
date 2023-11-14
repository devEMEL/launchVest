import { FormEvent, useEffect, useState, useRef } from 'react'
import { LaunchVestClient } from '../contracts/launch_vest'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk' 
import { VestStakeClient } from '../contracts/vest_stake'
import { useNavigate } from 'react-router-dom'

const ASSET_ID = 460043736

const Project = ({ project }) => {
  const [appId, setAppId] = useState<number>(479545536)
  const [assetName, setAssetName] = useState<string>('')
  const [imageURL, setImageURL] = useState<string>('')
  
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
  const navigate = useNavigate()

  const launchVestClient = new LaunchVestClient(
    {
      resolveBy: 'id',
      id: appId,
      sender,
    },
    algodClient,
  )

  const getAsset = async (assetID: number) => {
    const asset = await algodClient.getAssetByID(assetID).do()

    return asset.params.name
  }

  const getAssetAction = async () => {
    await getAsset(Number(project['asset id'])).then((data) => {
      console.log(data)
      setAssetName(data)
    })
  }
  const getAssetImage = async(ipfsLink) => {
    const CID = ipfsLink.split("//")[1]
    return ''.concat(`https://ipfs.io/ipfs/${CID}`)
  }
  const getAssetImageAction = async () => {
    await getAssetImage(project['image url']).then((data) => {
      setImageURL(data)
    })
  }
  const vestStakeClient = new VestStakeClient(
    {
      resolveBy: 'id',
      id: 479403066,
      sender,
    },
    algodClient,
  )
  const convertTimestampToDate = (timestamp: number) => {
    let dateFormat = new Date(timestamp * 1000)
    return ''.concat(
      dateFormat.getDate(),
      '/',
      dateFormat.getMonth() + 1,
      '/',
      dateFormat.getFullYear(),
      ' ',
      // ,
      // dateFormat.getHours(),
      // ":",
      // dateFormat.getMinutes(),
      // ":",
      // dateFormat.getSeconds()
    )
  }

  useEffect(() => {
    getAssetAction()
    getAssetImageAction()
  }, [])

  
  return (
    <div className="p-10 border-2 text-[20px] bg-black text-[#dddddd] rounded-[50px]">
      <h2 className="mb-2 text-center text-[25px]">{assetName}</h2>
      <div className="flex justify-center mt-5">
        <img src={imageURL} alt="" width={150} className='' />
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

        {/* <div className="capitalize p-2 flex justify-between">
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
        </div> */}
      </div>
      <div className="flex pt-10 justify-center">
        {/* <div className="basis-[50%] mr-5">
          <button className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full" onClick={() => handleBuy()}>
            Buy
          </button>
        </div> */}
        <div className="basis-[50%]">
          <button
            className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full"
            onClick={() => {
              navigate(`/project/${project['asset id']}`)
            }}
          >
            View project
          </button>
        </div>
      </div>
    </div>
  )
}

export default Project
