import { useWallet } from '@txnlab/use-wallet'
import { useDispatch, useSelector } from 'react-redux'
import { hideConnectModal } from '../../services/features/connectModal/connectModalSlice'
import { RootState } from '../../services/store/store'
import { Close } from '../Icons'
import { VestStakeClient } from '../../contracts/vest_stake'
import { getAlgodConfigFromViteEnvironment } from '../../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk'
import { useEffect, useState } from 'react'

const ConnectModal = () => {
  const [stakeBool, setStakeBool] = useState<boolean>(false)
  const [latestTimeStamp, setLatestTimeStamp] = useState<bigint>(0n)
  const [stakeDuration, setStakeDuration] = useState<bigint>(0n)

  const { showModal } = useSelector((store: RootState) => store.connectModal)
  const { providers } = useWallet()
  const dispatch = useDispatch()

  const { enqueueSnackbar } = useSnackbar()
  const { signer, activeAddress, activeAccount, connectedAccounts } = useWallet()
  const algodConfig = getAlgodConfigFromViteEnvironment()
  const algodClient = algokit.getAlgoClient({
    server: algodConfig.server,
    port: algodConfig.port,
    token: algodConfig.token,
  })

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const sender = { signer, addr: activeAddress! }

  const vestStakeClient = new VestStakeClient(
    {
      resolveBy: 'id',
      id: 460930743,
      sender,
    },
    algodClient,
  )
  // const getLatestTimeStamp = async () => {
  //   const status_ = await algodClient.status().do()
  //   const latestTimeStamp_ = await algodClient.block(status_['last-round']).do()
  //   setLatestTimeStamp(latestTimeStamp_['block']['ts'])
  // }
  // const checkIsStaking = async () => {
  //   let isStaking: boolean = false
  //   await getLatestTimeStamp()
  //   for (let _box of await vestStakeClient.appClient.getBoxNames()) {
  //     let result = await vestStakeClient.appClient.getBoxValue(_box)

  //     const resultCodec = algosdk.ABIType.from('(address,uint64,uint64,bool,uint64,uint64)')
  //     const stakingList = resultCodec.decode(result)
  //     console.log(stakingList[0])

  //     console.log(connectedAccounts)
  //     console.log(activeAccount?.address)

  //     if (stakingList[0] == activeAddress) {
  //       console.log('stakingList: ', stakingList[5])
  //       setStakeDuration(stakingList[5])

  //       console.log('latesttimestamp:', latestTimeStamp)
  //       console.log(stakingList[5])
  //       isStaking = true
  //       break
  //     }
  //   }
  //   return isStaking
  // }
  // const checkIsStakingAction = async () => {
  //   await checkIsStaking().then((state) => {
  //     console.log(state)
  //     setStakeBool(state)

  //     console.log(stakeBool)
  //   })
  // }

  // useEffect(() => {
  //  checkIsStakingAction()
  // }, [activeAddress])


  return (
    <>
      {showModal && (
        <div className="fixed w-full h-full bg-[#cbd5e1]" onClick={() => dispatch(hideConnectModal())}>
          <div
            className="max-w-[500px] w-full fixed top-[40%] left-[50%] -translate-x-[50%] -translate-y-[50%]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-white p-10">
              <div className="fixed top-[10%] right-[8%]">
                <button onClick={() => dispatch(hideConnectModal())}>
                  <Close />
                </button>
              </div>
              <div className="uppercase font-bold text-[30px] tracking-wide flex justify-center">connect your wallet</div>
              {/* List wallet providers */}
              <div className="mt-5 flex justify-between items-center">
                {providers?.map((provider) => (
                  <div key={provider.metadata.name} className="flex flex-col items-center">
                    <button
                      onClick={async () => {
                        dispatch(hideConnectModal())
                        await provider.connect()
                        
                        
                        
                      }}
                    >
                      <img
                        width={100}
                        height={30}
                        alt={`${provider.metadata.name} icon`}
                        src={provider.metadata.icon}
                        className="rounded-full"
                      />
                    </button>

                    <h2 className="mt-2">
                      {provider.metadata.name}
                      {provider.isActive && '[active]'}
                    </h2>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default ConnectModal
