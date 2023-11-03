import { configureStore } from '@reduxjs/toolkit'
import connectModalReducer from '../features/connectModal/connectModalSlice'
import confirmModalReducer from '../features/confirmModal/confirmModalSlice'

export const store = configureStore({
  reducer: {
    connectModal: connectModalReducer,
    confirmModal: confirmModalReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
