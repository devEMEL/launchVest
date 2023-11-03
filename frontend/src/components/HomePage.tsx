import React from 'react'
import { Logo } from './Icons'

const HomePage = () => {
  return (
    <div className="max-w-[90%] w-[100%] mx-auto">
      <div className="flex">
        <div className="uppercase text-[60px] basis-[50%] flex justify-center items-center">
          <div className="text-5xl font-extrabold bg-gradient-to-r from-black to-pink-600 bg-clip-text text-transparent">
            <span className="block mb-5">where projects</span> <span className="block text-black">take flight 🚀</span>
          </div>
        </div>
        <div className="basis-[50%] h-[80vh] bg-black">
          <Logo />
        </div>
      </div>

      <div className="mt-20 mb-20 px-20 py-[150px] bg-black text-white text-5xl font-extrabold bg-gradient-to-r from-black to-pink-600 rounded-[50px]">
		<div className='flex'>
			<div className='basis-[50%]'>Stay up to date on the latest news and IDOs</div>
              
			<div className='basis-[50%]'>
				<input type="text" placeholder='Email' className="text-black w-[100%] h-[60px] text-[16px] p-5 border-2 outline-0 bg-[#f8f6fe]" />
				<button className="capitalize w-[100%] bg-white py-4 text-black mt-5 text-[26px]">subscribe</button>
			</div>
		</div>
        
      </div>
    </div>
  )
}

export default HomePage
