import React, { useState, useRef, useEffect } from 'react'
import ConfirmModal from './Modals/ConfirmModal'
import { useDispatch } from 'react-redux'
import { showConfirmModal } from '../services/features/confirmModal/confirmModalSlice'
import { VestStakeClient } from '../contracts/vest_stake'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk, { Transaction } from 'algosdk'

const QUATERLY = 7_884_000n
const HALF_A_YEAR = 15_768_000n
const YEARLY = 31_536_000n

const ASSET_ID = 460043736

const Stake = () => {
  const _3months = useRef()
  const _6months = useRef()
  const _1year = useRef()
  const dispatch = useDispatch()
  const [amount, setAmount] = useState<bigint>(0n)
  const [stakeState, setStakeState] = useState<bigint>(0n)
  const [latestTimeStamp, setLatestTimeStamp] = useState<bigint>(0n)
  const [stakeDuration, setStakeDuration] = useState<bigint>(300n)

  const { enqueueSnackbar } = useSnackbar()
  const { signer, activeAddress, activeAccount } = useWallet()
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
      id: 460473489,
      sender,
    },
    algodClient,
  )
  // 100,000,000,000
  const stakeTxn = async () => {
    const decimals = (await algodClient.getAssetByID(ASSET_ID).do()).params.decimals
    // const stakeAmount = 200_000_000_000
    const stakeAmount = BigInt(amount) * BigInt(10 ** (decimals + 1))
    // stake
    console.log(stakeAmount)
    console.log(stakeDuration)

    const appAddress = (await vestStakeClient.appClient.getAppReference()).appAddress

    const txn = algosdk.makeAssetTransferTxnWithSuggestedParamsFromObject({
      from: String(activeAddress),
      to: appAddress,
      amount: BigInt(stakeAmount),
      assetIndex: ASSET_ID,
      suggestedParams: await algodClient.getTransactionParams().do(),
    })

    const tx = await vestStakeClient.stake(
      { asset: BigInt(ASSET_ID), stake_duration: BigInt(stakeDuration), txn },
      { boxes: [algosdk.decodeAddress(activeAddress).publicKey] },
    )
    console.log(tx)
  }

  const unstakeTxn = async () => {
    console.log('unstaking')
    const tx = await vestStakeClient.unStake({ asset: BigInt(ASSET_ID) }, { boxes: [algosdk.decodeAddress(activeAddress).publicKey] })
    console.log(tx);
  }

  const getLatestTimeStamp = async () => {
    const status_ = await algodClient.status().do()
    const latestTimeStamp_ = await algodClient.block(status_['last-round']).do()
    setLatestTimeStamp(latestTimeStamp_['block']['ts'])
  }
  const checkIsStaking = async () => {
    await getLatestTimeStamp()
    for (let _box of await vestStakeClient.appClient.getBoxNames()) {
      let result = await vestStakeClient.appClient.getBoxValue(_box)

      const resultCodec = algosdk.ABIType.from('(address,uint64,uint64,bool,uint64,uint64)')
      const stakingList = resultCodec.decode(result)
      console.log(stakingList[0])
      if (String(stakingList[0]) === activeAddress) {
        console.log('stakingList: ', stakingList[5])
        setStakeState(stakingList[5])

        console.log('latesttimestamp:', latestTimeStamp)
      }
    }
  }

  useEffect(() => {
    checkIsStaking()
  }, [])

  return (
    <div className="max-w-[60%] w-[100%] mx-auto">
      <div className="capitalize text-4xl flex justify-center py-5">Stake Vest</div>
      <div className="border-2 border-black-100 rounded-[50px] p-10 mb-10">
        <div className="mb-5">
          <label htmlFor="amount" className="text-2xl mr-5">
            Amount:
          </label>
          <input
            type="number"
            name="amount"
            id="amount"
            className="w-[85%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg"
            onChange={(e) => {
              setAmount(e.target.value as unknown as bigint)
            }}
          />
        </div>

        <div
          onClick={(e) => {
            console.log(e.target.id)
            if (e.target.id === '_3months') {
              _3months.current.style.backgroundColor = '#FFFFFF'
              _3months.current.style.color = '#000000'
              _3months.current.style.border = '4px solid black'
              _6months.current.style.backgroundColor = 'black'
              _6months.current.style.color = '#FFFFFF'
              _1year.current.style.backgroundColor = 'black'
              _1year.current.style.color = '#FFFFFF'
            }
            if (e.target.id === '_6months') {
              _6months.current.style.backgroundColor = '#FFFFFF'
              _6months.current.style.color = '#000000'
              _6months.current.style.border = '2px solid black'
              _3months.current.style.backgroundColor = 'black'
              _3months.current.style.color = '#FFFFFF'
              _1year.current.style.backgroundColor = 'black'
              _1year.current.style.color = '#FFFFFF'
            }
            if (e.target.id === '_1year') {
              _1year.current.style.backgroundColor = '#FFFFFF'
              _1year.current.style.color = '#000000'
              _1year.current.style.border = '2px solid black'
              _6months.current.style.backgroundColor = 'black'
              _6months.current.style.color = '#FFFFFF'
              _3months.current.style.backgroundColor = 'black'
              _3months.current.style.color = '#FFFFFF'
            }
          }}
          className="flex justify-center items-center my-20"
        >
          <button
            onClick={() => {
              setStakeDuration(QUATERLY)
            }}
          >
            <div
              id="_3months"
              ref={_3months}
              className="bg-black text-[26px] text-white mr-20 py-10 px-20 hover:text-[30px] hover:font-bold capitalize"
            >
              3 months
            </div>
          </button>
          <button
            onClick={() => {
              setStakeDuration(HALF_A_YEAR)
            }}
          >
            <div
              id="_6months"
              ref={_6months}
              className="bg-black text-[26px] text-white mr-20 py-10 px-20 hover:text-[30px] hover:font-bold capitalize"
            >
              6 months
            </div>
          </button>
          <button
            onClick={() => {
              setStakeDuration(YEARLY)
            }}
          >
            <div
              id="_1year"
              ref={_1year}
              className="bg-black text-[26px] text-white mr-20 py-10 px-20 hover:text-[30px] hover:font-bold capitalize "
            >
              1 year
            </div>
          </button>
        </div>

        <button
          type="submit"
          className="w-[100%] h-[60px] capitalize border-2 outline-0 rounded-full bg-[#000000] text-[26px] text-[#ffffff] font-bold shadow-lg shadow-indigo-500/40"
          onClick={
            Number(latestTimeStamp) > Number(stakeState)
              ? () => {
                  dispatch(showConfirmModal())
                }
              : () => {
                  dispatch(showConfirmModal())
                  // make sure stake duration is either of the 3 durations
                  // console.log(stakeDuration)
                }
          }
        >
          {Number(latestTimeStamp) > Number(stakeState) ? 'unstake' : 'stake'}
        </button>
      </div>
      {/* CONFIRM MODAL */}

      {/* <ConfirmModal {Number(latestTimeStamp) > Number(stakeState) ? text={`Stake ${amount} vest for ${stakeDuration === QUATERLY ? '3 months' : stakeDuration === HALF_A_YEAR ? '6 months' : '1 year'}`} : text="hello"}
txn={txn}
      /> */}
      {Number(latestTimeStamp) > Number(stakeState) ? (
        <ConfirmModal text={`Unstake vest`} txn={unstakeTxn} />
      ) : (
        <ConfirmModal
          text={`Stake ${amount} vest for ${
            stakeDuration === QUATERLY ? '3 months' : stakeDuration === HALF_A_YEAR ? '6 months' : '1 year'
          }`}
          txn={stakeTxn}
        />
      )}

      <button
        onClick={async () => {
          // await vestStakeClient.create.bare()
          // const vestStakeAppId = (await vestStakeClient.appClient.getAppReference()).appId
          // await vestStakeClient.appClient.fundAppAccount(algokit.microAlgos(300_000))
          // await vestStakeClient.bootstrap({ asset: BigInt(ASSET_ID) })

          // console.log(vestStakeAppId)

          // read box
          // let StakersArr = []
          for (let _box of await vestStakeClient.appClient.getBoxNames()) {
            let result = await vestStakeClient.appClient.getBoxValue(_box)

            const resultCodec = algosdk.ABIType.from('(address,uint64,uint64,bool,uint64,uint64)')
            const stakingList = resultCodec.decode(result)
            console.log('stakingList: ', stakingList[5])
            // let obj = {
            //   address: stakingList[0],
            //   amount: Number(stakingList[1]),
            //   assetId: Number(stakingList[2]),
            //   isStaking: stakingList[3],
            //   startTimestamp: Number(stakingList[4]),
            //   endTimestamp: Number(stakingList[5]),
            // }
            // StakersArr.push(obj)
          }
          // console.log(StakersArr)
          // return StakersArr

          // if currentTimestamp > endTimestamp (show unstake) else show stake
        }}
      >
        create staking app
      </button>
    </div>
  )
}

export default Stake
