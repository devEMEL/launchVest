import { useEffect, useState } from 'react'
import { LaunchVestClient } from '../contracts/launch_vest'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk'
import Project from './Project'

const projects_ = [
  {
    'asset id': 5,
    'asset price': 890,
    'start timestamp': 2345,
    'end timestamp': 456,
    'claim timestamp': 4567,
    'min buy': 1,
    'max buy': 6,
    'max cap': 456,
    'amount raised': 345,
    'assets for sale': 1234567,
    'assets sold': 4567889900,
  },{
    'asset id': 5,
    'asset price': 890,
    'start timestamp': 2345,
    'end timestamp': 456,
    'claim timestamp': 4567,
    'min buy': 1,
    'max buy': 6,
    'max cap': 456,
    'amount raised': 345,
    'assets for sale': 1234567,
    'assets sold': 4567889900,
  },
  {
    'asset id': 5,
    'asset price': 890,
    'start timestamp': 2345,
    'end timestamp': 456,
    'claim timestamp': 4567,
    'min buy': 1,
    'max buy': 6,
    'max cap': 456,
    'amount raised': 345,
    'assets for sale': 1234567,
    'assets sold': 4567889900,
  },
]

const Projects = () => {
  const [appId, setAppId] = useState<number>(464983859)
  const [projects, setProjects] = useState<Array<object>>([])
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
      let result = await launchVestClient.appClient.getBoxValue(_box)

      const resultCodec = algosdk.ABIType.from('(address,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,bool,bool,uint64,uint64)')
      const tokenList = resultCodec.decode(result)
      console.log(tokenList)
      let project = {
        'owner address': String(tokenList[0]),
        'start timestamp': Number(tokenList[1]),
        'end timestamp': Number(tokenList[2]),
        'claim timestamp': Number(tokenList[3]),
        'asset id': Number(tokenList[4]),
        'asset decimal': Number(tokenList[5]),
        'asset price': Number(tokenList[6]),
        'image url': String(tokenList[7]),
        'min buy': Number(tokenList[8]),
        'max buy': Number(tokenList[9]),
        'max cap': Number(tokenList[10]),
        'assets for sale': Number(tokenList[11]),
        'ispaused': tokenList[12],
        'initiated withdrawal': tokenList[13],
        'proceeds withdrawn': tokenList[14],
        'assets sold': Number(tokenList[15]),
        'amount raised': Number(tokenList[16]),
        'vesting schedule': Number(tokenList[17]),
        
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
    // handleShowProjectsAction()
    setProjects(projects_)
  }, [])

  return (
    <div className="max-w-[90%] w-[100%] m-auto">
      <div className="flex flex-wrap">
        {!!projects &&
          projects.map((project) => (
            <div className='basis-[33.3%] p-1 mb-5'>
              {/* DISPLAY ASSET NAME FROM ASSETINFO */}
              
              <Project project={project} key={project['asset id']} />
            </div>
          ))}
      </div>
      <button
        onClick={() => {
          handleShowProjectsAction()
        }}
      >
        handleShowProjectsAction
      </button>
    </div>
  )
}

export default Projects
