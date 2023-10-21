import { useWallet } from '@txnlab/use-wallet'
import { useDispatch } from 'react-redux'
import { showConnectModal } from '../services/features/connectModal/connectModalSlice'
import { ellipseAddress } from '../utils/ellipseAddress'

const Navbar = () => {
  const dispatch = useDispatch()
  const { activeAccount, activeAddress, providers } = useWallet()

  const disconnectWallet = async () => {
	if(providers) {
		const activeProvider = providers.find(p => p.isActive);
		if(activeProvider) {
			activeProvider.disconnect();
		}
	}
    providers?.map((provider) => provider.disconnect())
  }
  return (
    <nav className="max-w-[90%] w-[100%] mx-auto py-5 capitalize bg-white text-black w-full">
      <div className="flex justify-between items-center">
        <div className="text-[40px]">LaunchVest</div>
        <div className="flex items-center">
          {activeAccount && (
            <button className="capitalize bg-white text-black py-4 px-10 rounded-full">
              {ellipseAddress(activeAddress)}
            </button>
          )}

          <button
            className="capitalize bg-black text-white py-4 px-10 rounded-full"
            onClick={!activeAccount ? () => dispatch(showConnectModal()) : () => disconnectWallet()}
          >
            {!activeAccount ? 'connect your wallet' : 'Disconnect Wallet'}
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
