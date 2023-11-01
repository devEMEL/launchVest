import { FormEvent, useEffect, useState, useRef } from 'react'
import { LaunchVestClient } from '../contracts/launch_vest'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk'
import { VestStakeClient } from '../contracts/vest_stake'

const ASSET_ID = 460043736

const Project = ({ project }) => {
  const [appId, setAppId] = useState<number>(0)
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

  const vestStakeClient = new VestStakeClient(
    {
      resolveBy: 'id',
      id: 462048462,
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

  const handleBuy = async () => {
    // isStaking, asset id, paymentTxn
    // read box and check whether address has isStaking true;

    // let projectsArr = []
    // for (let _box of await launchVestClient.appClient.getBoxNames()) {
    //   console.log(Buffer.from(_box.nameRaw, 'base64').toString('utf8'))
    //   let result = await launchVestClient.appClient.getBoxValue(_box)

    // }
    const tokenKey = algosdk.encodeUint64(BigInt(project['asset id']))
    const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
      from: String(activeAddress),
      to: String(project['owner address']),
      amount: BigInt(6_000_000),
      suggestedParams: await algodClient.getTransactionParams().do(),
    })

    const tx = await launchVestClient.invest(
      { is_staking: Boolean(true), project: BigInt(project['asset id']), txn },
      {
        boxes: [algosdk.decodeAddress(activeAddress).publicKey, tokenKey],
      },
    )
    console.log(tx)
  }
  return (
    <div className="p-10 border-2 text-[20px] bg-black text-[#dddddd] rounded-[50px]">
      <h2 className="mb-2 text-center text-[25px]">ASSET NAME</h2>
      {/* {Object.entries(project).map((res) => (
        <div className="capitalize p-2 flex justify-between">
          <h1>{res[0]}</h1>
          <h1>{res[1]}</h1>
        </div>
      ))} */}
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
          <button className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full" onClick={() => handleBuy()}>
            Buy
          </button>
        </div>
        <div className="basis-[50%]">
          <button className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full">claim</button>
        </div>
      </div>
    </div>
  )
}

export default Project
