import { useWallet } from '@txnlab/use-wallet'
import React, { useState } from 'react'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { LaunchVestClient } from '../contracts/launch_vest'
import algosdk from 'algosdk'
import { useSnackbar } from 'notistack'

const Withdraw = () => {
  const [projectId, setProjectId] = useState<bigint>(0n)
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
      id: 479545536,
      sender,
    },
    algodClient,
  )
  return (
    <div className="max-w-[60%] w-[100%] mx-auto">
      <div className="mt-3">
        <input
          type="text"
          placeholder="Enter Project ID"
          name="project_id"
          id="project_id"
          className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg"
          onChange={(e) => {
            setProjectId(e.target.value as unknown as bigint)
          }}
        />
      </div>
      <button
        type="submit"
        onClick={async (e) => {
          e.preventDefault()
          await launchVestClient.withdrawAmountRaised(
            { project_id: BigInt(projectId) },
            {
              boxes: [algosdk.encodeUint64(BigInt(projectId))],
            },
          )
		  .then(() => {
			enqueueSnackbar(`Withdrawal success.`, { variant: 'success' })
		  })
		  .catch((err) => {
			enqueueSnackbar(`Withdrawal failed: ${(err as Error).message}`, { variant: 'error' })
		  })
        }}
        className="w-[100%] h-[50px] border-2 my-5 outline-0 rounded-full bg-[#000000] text-[16px] text-[#ffffff] font-bold shadow-lg shadow-indigo-500/40"
      >
        submit
      </button>
    </div>
  )
}

export default Withdraw
