const ListToken = () => {
  return (
    <div className="max-w-[60%] w-[100%] mx-auto">
      <div className="capitalize text-4xl flex justify-center py-5">list token</div>
      <div className="border-2 border-black-100 rounded-[50px] p-10 mb-10">
        <form onSubmit={(e) => {e.preventDefault()}}>
          <div className="mb-5">
            <label htmlFor="token__name" className="text-2xl">
              Token Name
            </label>
            <div className="my-[30px]">
              <input
                type="text"
                name="token__name"
                id="token__name"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="token__name" className="text-2xl">
              Token Name
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="token__name"
                id="token__name"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
              />
            </div>
          </div>

          <div className="mb-5">
            <label htmlFor="token__name" className="text-2xl">
              Token Name
            </label>
            <div className="mt-3">
              <input
                type="text"
                name="token__name"
                id="token__name"
                className="w-[100%] h-[50px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe] rounded-lg "
              />
            </div>
          </div>

		  <button type="submit" className="w-[100%] h-[45px] border-2 outline-0 rounded-full bg-[#000000] text-[16px] text-[#ffffff] font-bold shadow-lg shadow-indigo-500/40">Submit</button>
        </form>
      </div>
    </div>
  )
}

export default ListToken
