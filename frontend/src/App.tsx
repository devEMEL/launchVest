import { DeflyWalletConnect } from '@blockshake/defly-connect'
import { DaffiWalletConnect } from '@daffiwallet/connect'
import { PeraWalletConnect } from '@perawallet/connect'
import { PROVIDER_ID, ProvidersArray, WalletProvider, useInitializeProviders, useWallet } from '@txnlab/use-wallet'
import algosdk from 'algosdk'
import { SnackbarProvider } from 'notistack'
import Footer from './components/Footer'
import ConnectModal from './components/Modals/ConnectModal'
import Navbar from './components/Navbar'
import { getAlgodConfigFromViteEnvironment } from './utils/network/getAlgoClientConfigs'
import ListToken from './components/ListToken'

let providersArray: ProvidersArray

providersArray = [
  { id: PROVIDER_ID.DEFLY, clientStatic: DeflyWalletConnect },
  { id: PROVIDER_ID.PERA, clientStatic: PeraWalletConnect },
  { id: PROVIDER_ID.DAFFI, clientStatic: DaffiWalletConnect },
  { id: PROVIDER_ID.EXODUS },
]

export default function App() {
  const { activeAddress } = useWallet()

  const algodConfig = getAlgodConfigFromViteEnvironment()

  const walletProviders = useInitializeProviders({
    providers: providersArray,
    nodeConfig: {
      network: algodConfig.network,
      nodeServer: algodConfig.server,
      nodePort: String(algodConfig.port),
      nodeToken: String(algodConfig.token),
    },
    algosdkStatic: algosdk,
  })

  return (
    <SnackbarProvider maxSnack={3}>
      <WalletProvider value={walletProviders}>
        <div className="w-full h-full">
          {/* NAVBAR */}
          <Navbar />
          {/* MODALS */}
          <ConnectModal />

          {/* ROUTES */}
          <ListToken />

          {/* FOOTER */}
          <Footer />
        </div>
      </WalletProvider>
    </SnackbarProvider>
  )
}
