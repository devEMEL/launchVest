import { Link } from 'react-router-dom'
import { Discord, Twitter } from './Icons'

const Footer = () => {
  return (
    <div className="bg-black">
      <div className="w-[90%] mx-auto pt-24 pb-12 capitalize text-white">
        <div className="w-[80%]  mx-auto mb-20 flex justify-between items-center">
          <div className="">
            <p>Home</p>
            <p>
              <Link to='/list-token'>List Token</Link>
            </p>
            <p>
              <Link to='/projects'>Projects</Link>
            </p>
          </div>
          <div>
            <p></p>
          </div>
          <div>
            <p></p>
          </div>
        </div>
        <div className="flex justify-center items-center">
          <a href="https://google.com" target="blank" className="mr-3 -mt-1.5">
            <Twitter />
          </a>
          <a href="https://google.com" target="blank">
            <Discord />
          </a>
        </div>
      </div>
    </div>
  )
}

export default Footer
