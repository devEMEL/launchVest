import React, { useState, useRef, useEffect } from 'react'
import ConfirmModal from './Modals/ConfirmModal'
import { useDispatch } from 'react-redux'
import { showConfirmModal } from '../services/features/confirmModal/confirmModalSlice'
import { VestStakeClient } from '../contracts/vest_stake'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import algosdk from 'algosdk'

const QUATERLY = 7_776_000n
const HALF_A_YEAR = 15_552_000n
const YEARLY = 31_536_000n

const ASSET_ID = 460043736

const Stake = () => {
  const _3months = useRef()
  const _6months = useRef()
  const _1year = useRef()
  const dispatch = useDispatch()
  const [amount, setAmount] = useState<bigint>(0n)
  const [stakeType, setStakeType] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(false)

  const [stakeDuration, setStakeDuration] = useState<bigint>(0n)

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

  const vestStakeClient = new VestStakeClient(
    {
      resolveBy: 'id',
      id: 479773538,
      sender,
    },
    algodClient,
  )
  // 100,000,000,000
  const stakeTxn = async () => {
    const decimals = (await algodClient.getAssetByID(ASSET_ID).do()).params.decimals
    // const stakeAmount = 200_000_000_000
    const stakeAmount = BigInt(amount) * BigInt(10 ** decimals)
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
    return tx
  }

  const unstakeTxn = async () => {
    console.log('unstaking')
    const tx = await vestStakeClient.unStake({ asset: BigInt(ASSET_ID) }, { boxes: [algosdk.decodeAddress(activeAddress).publicKey] })
    console.log(tx)
    return tx
  }

  const stakeTxnAction = async () => {
    // on error alert ('Error staking! Ensure you have enough funds or are not currently staking')
    setLoading(true)
    await stakeTxn()
      .then(() => {
        enqueueSnackbar(`Staked successfully.`, { variant: 'success' })
        setLoading(false)
      })
      .catch((err) => {
        enqueueSnackbar(`Error staking: ${(err as Error).message}`, { variant: 'error' })
        setLoading(false)
      })
  }

  const unstakeTxnAction = async () => {
    // on error alert ('Error staking! Ensure you have enough funds or are not currently staking')
    setLoading(true)
    await unstakeTxn()
      .then(() => {
        enqueueSnackbar(`Unstaked successfully.`, { variant: 'success' })
        setLoading(false)
      })
      .catch((err) => {
        enqueueSnackbar(`Error unstaking: ${(err as Error).message}`, { variant: 'error' })
        setLoading(false)
      })
  }

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
              className="bg-black text-[26px] text-white mr-20 py-10 px-20 hover:text-[30px] hover:font-bold capitalize"
            >
              1 year
            </div>
          </button>
        </div>

        <button
          type="submit"
          className="w-[100%] h-[60px] capitalize border-2 outline-0 rounded-full bg-[#000000] text-[26px] text-[#ffffff] font-bold shadow-lg shadow-indigo-500/40"
          onClick={
            Number(amount) == 0 || Number(stakeDuration) == 0
              ? () => {
                  // alert error
                  console.log('no duration selected');
                  enqueueSnackbar(`Error staking, make sure amount and duration are selected:`, { variant: 'error' })
                }
              : () => {
                  dispatch(showConfirmModal())
                  setStakeType(1)
                }
          }
        >
          stake
        </button>
        <button
          type="submit"
          className="w-[100%] h-[60px] capitalize border-2 outline-0 rounded-full bg-[#000000] text-[26px] text-[#ffffff] font-bold shadow-lg shadow-indigo-500/40"
          onClick={() => {
            dispatch(showConfirmModal())
            setStakeType(0)
          }}
        >
          unstake
        </button>
      </div>
      {/* CONFIRM MODAL */}
      {stakeType == 1 ? (
        <ConfirmModal
          text={`Stake ${amount} vest for ${
            stakeDuration === QUATERLY
              ? '3 months'
              : stakeDuration === HALF_A_YEAR
              ? '6 months'
              : stakeDuration === YEARLY
              ? '1 year'
              : 'invalid duration'
          }`}
          txn={stakeTxnAction}
        />
      ) : (
        <ConfirmModal text={`Unstake vest`} txn={unstakeTxnAction} />
      )}

      {/* <button
        onClick={async () => {
          await vestStakeClient.create.bare()
          const vestStakeAppId = (await vestStakeClient.appClient.getAppReference()).appId
          await vestStakeClient.appClient.fundAppAccount(algokit.microAlgos(300_000))
          await vestStakeClient.bootstrap({ asset: BigInt(ASSET_ID) }, { sendParams: { fee: algokit.microAlgos(200_000) }})

          console.log(vestStakeAppId)

          // read box
          let StakersArr = []
          // this below
          for (let _box of await vestStakeClient.appClient.getBoxNames()) {
            let result = await vestStakeClient.appClient.getBoxValue(_box)

            const resultCodec = algosdk.ABIType.from('(address,uint64,uint64,bool,uint64,uint64)')
            const stakingList = resultCodec.decode(result)
            console.log('stakingList: ', stakingList[5])
          // this above
          let obj = {
            address: stakingList[0],
            amount: Number(stakingList[1]),
            assetId: Number(stakingList[2]),
            isStaking: stakingList[3],
            startTimestamp: Number(stakingList[4]),
            endTimestamp: Number(stakingList[5]),
          }
          StakersArr.push(obj)
          // this below
          }
          // this above
          console.log(StakersArr)
          return StakersArr

          if currentTimestamp > endTimestamp (show unstake) else show stake
        }}
      >
         create staking app
      </button> */}
    </div>
  )
}

export default Stake
