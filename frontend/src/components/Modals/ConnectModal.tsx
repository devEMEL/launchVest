import { useWallet } from '@txnlab/use-wallet'
import { useDispatch, useSelector } from 'react-redux'
import { hideConnectModal } from '../../services/features/connectModal/connectModalSlice'
import { RootState } from '../../services/store/store'
import { Close } from '../Icons'

const ConnectModal = () => {
  const { showModal } = useSelector((store: RootState) => store.connectModal)
  const { providers } = useWallet()
  const dispatch = useDispatch()
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
