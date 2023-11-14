import { useWallet } from '@txnlab/use-wallet'
import { useDispatch } from 'react-redux'
import { showConnectModal } from '../services/features/connectModal/connectModalSlice'
import { ellipseAddress } from '../utils/ellipseAddress'
import { Link, useNavigate } from 'react-router-dom'

const Navbar = () => {
  const dispatch = useDispatch()
  const { activeAccount, activeAddress, providers } = useWallet()

  const navigate = useNavigate()
  const disconnectWallet = async () => {
    if (providers) {
      const activeProvider = providers.find((p) => p.isActive)
      if (activeProvider) {
        activeProvider.disconnect()
      }
    }
    providers?.map((provider) => provider.disconnect())
  }

  return (
    <nav className="max-w-[90%] w-[100%] mx-auto py-5 capitalize bg-white text-black w-full mb-10">
      <div className="flex justify-between items-center">
        <div className="text-[40px]"><Link to="/">LaunchVest</Link></div>
        <div className="">
          <button className="capitalize mr-5 pb-1 border-b-2 border-black">
            <Link to="/list-project">list project</Link>
          </button>
          <button className="capitalize mr-5 pb-1 border-b-2 border-black">
            <Link to="/stake">Stake</Link>
          </button>
          <button className="capitalize mr-5 pb-1 border-b-2 border-black">
            <Link to="/projects">projects</Link>
          </button>
          {activeAccount && (
            <button className="capitalize bg-white text-black py-4 px-10 rounded-full">{ellipseAddress(activeAddress)}</button>
          )}

          <button
            className="capitalize bg-black text-white py-4 px-10 rounded-full"
            onClick={!activeAccount ? () => dispatch(showConnectModal()) : () => {
              disconnectWallet()
              navigate("/")
            }}
          >
            {!activeAccount ? 'connect your wallet' : 'Disconnect Wallet'}
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
