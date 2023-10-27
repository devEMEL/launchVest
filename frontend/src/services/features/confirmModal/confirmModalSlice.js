import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  showModal: false,
};

const confirmModalSlice = createSlice({
  name: "confirmModal",
  initialState,
  reducers: {
    showConfirmModal: (state) => {
      state.showModal = true;
    },
    hideConfirmModal: (state) => {
      state.showModal = false;
    },
  },
});
export const { showConfirmModal, hideConfirmModal } = confirmModalSlice.actions;
export default confirmModalSlice.reducer;
