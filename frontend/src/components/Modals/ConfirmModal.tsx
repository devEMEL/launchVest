import { useDispatch, useSelector } from 'react-redux'
import { hideConfirmModal } from '../../services/features/confirmModal/confirmModalSlice'
import { RootState } from '../../services/store/store'
import { useSnackbar } from 'notistack'
import { useState } from 'react'

const ConfirmModal = ({ text, txn }) => {
  const [loading, setLoading] = useState<boolean>(false)
  const { showModal } = useSelector((store: RootState) => store.confirmModal)
  const dispatch = useDispatch()
  const { enqueueSnackbar } = useSnackbar()
  return (
    <div>
      {showModal && (
        <div className="fixed w-full h-full top-[0] left-[0]">
          <div className="max-w-[400px] bg-black text-white p-10 w-full fixed top-[40%] left-[50%] -translate-x-[50%] -translate-y-[50%]">
            <div className="text-[20px] text-center font-bold">{text}</div>
            <div className="flex justify-between items-center mt-5">
              <button className="p-3 border-2 bg-white text-black capitalize" onClick={() => dispatch(hideConfirmModal())}>
                cancel
              </button>
              <button
                className="p-3 border-2 bg-white text-black capitalize"
                onClick={() => {
                  dispatch(hideConfirmModal())
                  // call function
                  txn()
                }}
              >
                submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ConfirmModal
