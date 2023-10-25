import { useEffect, useState } from 'react'
import { LaunchVestClient } from '../contracts/launch_vest'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk'


const Projects = () => {
  const [appId, setAppId] = useState<number>(454968947)
  const [projects, setProjects] = useState<Array<object>>([]);
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


  const handleShowProjects = async () => {
    console.log('handleShowProjects')

    let projectsArr = []
    for (let _box of await launchVestClient.appClient.getBoxNames()) {
      let result = await launchVestClient.appClient.getBoxValue(_box.name)
      let key = _box.nameRaw;
      console.log(key)
      console.log(result)

      const resultCodec = algosdk.ABIType.from('(address,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,bool,bool,uint64,uint64)')
      const tokenList = resultCodec.decode(result)
      console.log(tokenList)
      let project = {
        tokenPrice: Number(tokenList[4]),
        minimumBuy: Number(tokenList[5]),
        maximumBuy: Number(tokenList[6]),
        startTime: Number(tokenList[1]),
        endTime: Number(tokenList[2]),
        claimTime: Number(tokenList[3]),
        AmountRaised: Number(tokenList[12]),
        TotalTokenSold: Number(tokenList[11]),
      }
      projectsArr.push(project)
    }
    return projectsArr
  }

  const handleShowProjectsAction = async () => {
    await handleShowProjects().then((projects) => {
      console.log(projects)
      setProjects(projects)
    })
  }

  useEffect(() => {
    handleShowProjectsAction()
  }, [])
  return (
    <div>
      {/* {!!projects && projects.map(project => (
        <div key={project.assetId}>

        </div>
      ))} */}
      hello people

    </div>

  )
}

export default Projects;
