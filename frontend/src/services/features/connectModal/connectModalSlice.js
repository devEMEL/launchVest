import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  showModal: false,
};

const connectModalSlice = createSlice({
  name: "connectModal",
  initialState,
  reducers: {
    showConnectModal: (state) => {
      state.showModal = true;
    },
    hideConnectModal: (state) => {
      state.showModal = false;
    },
  },
});
export const { showConnectModal, hideConnectModal } = connectModalSlice.actions;
export default connectModalSlice.reducer;
