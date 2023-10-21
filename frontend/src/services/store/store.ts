import { configureStore } from '@reduxjs/toolkit'
import connectModalReducer from '../features/connectModal/connectModalSlice'

export const store = configureStore({
  reducer: {
    connectModal: connectModalReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
