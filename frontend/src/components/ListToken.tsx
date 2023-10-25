import { FormEvent, useState } from 'react'
import { LaunchVestClient } from '../contracts/launch_vest'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk'

const ListToken = () => {
  const [appId, setAppId] = useState<number>(0)
  const [assetId, setAssetId] = useState<bigint>(0n)
  const [startTimestamp, setStartTimestamp] = useState<bigint>(0n)
  const [endTimestamp, setEndTimestamp] = useState<bigint>(0n)
  const [claimTimestamp, setClaimTimestamp] = useState<bigint>(0n)
  const [assetPrice, setAssetPrice] = useState<bigint>(0n)
  const [minimumBuy, setMinimumBuy] = useState<bigint>(0n)
  const [maximumBuy, setMaximumBuy] = useState<bigint>(0n)

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
    console.log(launchVestAppId)
  }
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!(assetId && startTimestamp && endTimestamp && claimTimestamp && assetPrice && minimumBuy && maximumBuy && maxCap)) return

    const listToken = await launchVestClient.listProject({
      asset_id: assetId,
      start_timestamp: startTimestamp,
      end_timestamp: endTimestamp,
      claim_timestamp: claimTimestamp,
      asset_price: assetPrice,
      max_investment_per_user: maximumBuy,
      min_investment_per_user: minimumBuy
    }, {})
  }
  return (
    <div className="max-w-[60%] w-[100%] mx-auto">
      <div className="capitalize text-4xl flex justify-center py-5">list token</div>
      <div className="border-2 border-black-100 rounded-[50px] p-10 mb-10">
        <form onSubmit={(e) => handleSubmit(e)}>
          <div className="mb-5">
            <label htmlFor="asset_id" className="text-2xl">
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
            <label htmlFor="start__timestamp" className="text-2xl">
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
            <label htmlFor="end__timestamp" className="text-2xl">
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
            <label htmlFor="claim__timestamp" className="text-2xl">
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
            <label htmlFor="asset__price" className="text-2xl">
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
            <label htmlFor="minimum__buy" className="text-2xl">
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
            <label htmlFor="maximum__buy" className="text-2xl">
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
            <label htmlFor="max__cap" className="text-2xl">
              Max Cap
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="max__cap"
                id="max__cap"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
                onChange={(e) => {
                  setMaxCap(e.target.value as unknown as bigint), console.log(maxCap)
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-[100%] h-[45px] border-2 outline-0 rounded-full bg-[#000000] text-[16px] text-[#ffffff] font-bold shadow-lg shadow-indigo-500/40"
          >
            Submit
          </button>
        </form>
      </div>

      <button onClick={() => handleCreate()}>create app</button>
    </div>
  )
}

export default ListToken
