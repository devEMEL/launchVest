import React from 'react'

const Project = ({ project }) => {
  return (
    <div className="p-10 border-2 text-[20px] bg-black text-[#dddddd] rounded-[50px]">
      <h2 className="mb-2 text-center text-[25px]">ASSET NAME</h2>
      {/* {Object.entries(project).map((res) => (
        <div className="capitalize p-2 flex justify-between">
          <h1>{res[0]}</h1>
          <h1>{res[1]}</h1>
        </div>
      ))} */}
      <div className="">
        <div className="capitalize p-2 flex justify-between">
          <h1>asset id</h1>
          <h1>{project['asset id']}</h1>
        </div>
        <div className="capitalize p-2 flex justify-between">
          <h1>asset price</h1>
          <h1>{project['asset price']}</h1>
        </div>
        <div className="capitalize p-2 flex justify-between">
          <h1>start timestamp</h1>
          <h1>{project['asset price']}</h1>
        </div>
        <div className="capitalize p-2 flex justify-between">
          <h1>end timestamp</h1>
          <h1>{project['start timestamp']}</h1>
        </div>
        <div className="capitalize p-2 flex justify-between">
          <h1>claim timestamp</h1>
          <h1>{project['claim timestamp']}</h1>
        </div>

        <div className="capitalize p-2 flex justify-between">
          <h1>min buy</h1>
          <h1>{project['min buy']}</h1>
        </div>
        <div className="capitalize p-2 flex justify-between">
          <h1>max buy</h1>
          <h1>{project['max buy']}</h1>
        </div>

        <div className="capitalize p-2 flex justify-between">
          <h1>max cap</h1>
          <h1>{project['max cap']}</h1>
        </div>
        <div className="capitalize p-2 flex justify-between">
          <h1>amount raised</h1>
          <h1>${project['amount raised']}</h1>
        </div>
        <div className="capitalize p-2 flex justify-between">
          <h1>assets for sale</h1>
          <h1>{project['assets for sale']}</h1>
        </div>
        <div className="capitalize p-2 flex justify-between">
          <h1>assets sold</h1>
          <h1>{project['assets sold']}</h1>
        </div>
      </div>
      <div className="flex pt-10">
        <div className="basis-[50%] mr-5">
          <button className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full">Buy</button>
        </div>
        <div className="basis-[50%]">
          <button className="w-full capitalize bg-[#dddddd] text-black py-4 px-10 rounded-full">claim</button>
        </div>
      </div>
    </div>
  )
}

export default Project
