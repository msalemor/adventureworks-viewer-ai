import { useEffect, useState } from 'react'
import 'react-data-grid/lib/styles.css';
import DataGrid, { SortColumn } from 'react-data-grid';
import axios from 'axios'
import { RiSendPlane2Fill } from "react-icons/ri"
import { MdOutlineClear } from "react-icons/md"
import { Puff } from 'react-loader-spinner'
import { BsPersonFill } from "react-icons/bs"
import { BsPersonFillUp } from "react-icons/bs"
import { RiProductHuntLine } from "react-icons/ri"
import { RiProductHuntFill } from "react-icons/ri"
import { GiCargoCrate } from "react-icons/gi"
import { ICounts, IGridColsRow, IMessage, IResponse, ISettings, Mode } from './intefaces';
import { IoMdInformationCircleOutline } from "react-icons/io"


const URL_BASE = import.meta.env.VITE_BASE_URL
//const URL_BASE = ''

const Settings = {
  mode: Mode.Chatbot,
  max_token: '500',
  temperature: '0.3',
}
const Counts = {
  customers: 0,
  topCustomers: 0,
  products: 0,
  topProducts: 0,
  orderDetails: 0
}

function App2() {

  // state
  const [settings, setSettings] = useState<ISettings>(Settings)
  const [processing, setProcessing] = useState(false)
  const [gridColsRow, setGridColsRow] = useState<IGridColsRow>({ columns: [], rows: [] })
  const [sortColumns, setSortColumns] = useState<readonly SortColumn[]>([]);
  const [recordCounts, setRecordCounts] = useState<ICounts>(Counts)
  const [input, setInput] = useState<string>('')
  const [messages, setMessages] = useState<IMessage[]>([])

  // effetcs
  useEffect(() => {
    (async () => {
      try {
        let resp = await axios.get<ICounts>(URL_BASE + '/api/counts')
        console.info(resp.data)
        setRecordCounts(resp.data)
      }
      catch (error) {
        console.error(error)
      }
    })()
  }, [])

  // supporting functions
  const getGridDate = async (evt: any, target: string) => {
    evt.preventDefault();

    if (processing) return
    try {
      setProcessing(true)
      setGridColsRow({ columns: [], rows: [] })
      let url = ''
      switch (target) {
        case 'customers':
          url = URL_BASE + '/api/customers'
          break
        case 'sales':
          url = URL_BASE + '/api/customers/top'
          break
        case 'products':
          url = URL_BASE + '/api/products'
          break
        case 'sold':
          url = URL_BASE + '/api/products/sold'
          break
        case 'orders':
          url = URL_BASE + '/api/orders'
          break
        default:
          break
      }
      let resp = await axios.get<IGridColsRow>(url)
      const colrows = resp.data
      setGridColsRow(colrows)
    }
    catch (error) {
      console.error(error)
    }
    finally {
      setProcessing(false)
    }
  }

  const Process = async () => {
    if (processing) return
    setProcessing(true)

    try {
      const payload = { input: input }
      let URL = URL_BASE

      if (settings.mode === Mode.Chatbot) {
        URL = URL_BASE + '/api/chatbot'
      } else if (settings.mode === Mode.SqlBot) {
        URL = URL_BASE + '/api/sqlbot'
      } else if (settings.mode === Mode.Assistant) {
        URL = URL_BASE + '/api/assistants'
      } else if (settings.mode === Mode.MultiAgent) {
        URL = URL_BASE + '/api/multiagent'
      }

      if (URL === URL_BASE)
        throw new Error('Invalid mode')

      const resp = await axios.post<IResponse[]>(URL, payload)
      const data = resp.data

      data.forEach((msg: IResponse) => {
        setMessages([...messages, { role: msg.role, content: msg.content, imageUrl: null, mode: (msg.role === "assistant" ? settings.mode : null) }])
        if (msg.rows && msg.rows.length > 0) {
          setGridColsRow({ columns: msg.columns, rows: msg.rows })
          setMessages([...messages, { role: msg.role, content: msg.content, imageUrl: null, mode: (msg.role === "assistant" ? settings.mode : null) }])
        }
      })

    }
    catch (error) {
      console.error(error)
    }
    finally {
      setInput('')
      setProcessing(false)
    }
  }

  const getModeHelp = () => {
    switch (settings.mode) {
      case Mode.Chatbot:
        return 'Connected to top customers and products.\nSamples:\nWrite a demand letter to the customer with the highest balance?\nWhat are the top 5 products sold?'
      case Mode.SqlBot:
        return "Connected to all tables.\nSamples:\nWhat customers are in the United States?\nWhat products have 'bike' in the description?"
      case Mode.Assistant:
        return 'Connected to top customers and products.\nSamples:\nCreate a chart of the sales by country.\nWhat are the top 5 products sold?'
      case Mode.MultiAgent:
        return 'Connected to top customers, products, weather, and shipping costs.'
      default:
        return 'No AI mode'
    }
  }

  // JSX
  return (
    <>
      <header className="bg-slate-950 h-[40px] text-white p-2 flex items-center">
        <h1 className="text-xl font-bold">AdventureWorks Viewer</h1>
      </header>

      <nav className="h-[35px] bg-slate-900 flex text-white items-center space-x-3 p-2">
        <label>Mode: </label>

        <input type="radio" name="opt1" id='simple'
          checked={settings.mode === Mode.NoAI}
          onChange={() => setSettings({ ...settings, mode: Mode.NoAI })}
        />
        <label htmlFor='simple'>No AI</label>

        <input type="radio" name="opt1" id='chatbot'
          checked={settings.mode === Mode.Chatbot}
          onChange={() => setSettings({ ...settings, mode: Mode.Chatbot })}
        />
        <label htmlFor='chatbot'>Chatbot</label>

        <input type="radio" name="opt1" id='sqlbot'
          checked={settings.mode === Mode.SqlBot}
          onChange={() => setSettings({ ...settings, mode: Mode.SqlBot })}
        />
        <label htmlFor='sqlbot'>Sqlbot</label>

        <input type="radio" name="opt1" id='assistants'
          checked={settings.mode === Mode.Assistant}
          onChange={() => setSettings({ ...settings, mode: Mode.Assistant })}
        />
        <label htmlFor='assistants'>Assistants API</label>

        <input type="radio" name="opt1" id='multiagent'
          checked={settings.mode === Mode.MultiAgent}
          onChange={() => setSettings({ ...settings, mode: Mode.MultiAgent })}
        />
        <label htmlFor='multiagent'>Multi-agent</label>
      </nav>

      {/* Grid selection boxes */}
      <section className='h-[100px] flex space-x-1 bg-slate-900'>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer hover:bg-blue-500'
          onClick={(evt) => getGridDate(evt, 'customers')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.customers}</label>
          <label className='font-semibold uppercase text-3xl'><BsPersonFill title='Customers' /></label>
        </div>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer hover:bg-blue-500'
          onClick={(evt) => getGridDate(evt, 'sales')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.topCustomers}</label>
          <label className='font-semibold uppercas text-3xl'><BsPersonFillUp title='Top Customers' /></label>
        </div>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer hover:bg-blue-500'
          onClick={(evt) => getGridDate(evt, 'products')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.products}</label>
          <label className='font-semibold uppercase text-3xl'><RiProductHuntLine title='Products' /></label>
        </div>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer hover:bg-blue-500'
          onClick={(evt) => getGridDate(evt, 'sold')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.topProducts}</label>
          <label className='font-semibold uppercase text-3xl'><RiProductHuntFill title='Top Products' /></label>
        </div>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer hover:bg-blue-500'
          onClick={(evt) => getGridDate(evt, 'orders')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.orderDetails}</label>
          <label className='font-semibold uppercase text-3xl'><GiCargoCrate title='Orders' /></label>
        </div>
      </section>

      <div className="h-[calc(100vh-75px-35px-100px)] flex flex-wrap">
        <main className={'bg-slate-200 ' + (settings.mode == Mode.NoAI ? 'w-full' : 'w-2/3')}>
          <DataGrid
            sortColumns={sortColumns}
            onSortColumnsChange={setSortColumns}
            className='h-[calc(100vh-75px-35px-100px)]' columns={gridColsRow.columns} rows={gridColsRow.rows} />
        </main>
        <aside className={(settings.mode === Mode.NoAI ? 'invisible' : 'md:w-1/3 flex flex-col')}>
          <div className='h-[calc(100vh-75px-35px-100px-150px)] flex flex-col overflow-auto p-2 space-y-2'>
            {messages.map((msg, idx) => <>
              {msg.role === 'user' && <div key={idx} className='bg-slate-200 p-2 rounded-lg w-[90%] ml-auto'>
                {msg.content}
              </div>}
              {msg.role === 'assistant' && <div key={idx} className='bg-slate-300 p-2 rounded-lg w-[90%]'>
                <span className='font-semibold'>{msg.mode}: </span>{msg.content}</div>}
              {msg.role === 'image' && <div>
                <img key={idx} src={msg.content ? URL_BASE + msg.content : ""} alt='this is an image that was generated by Assistants API' />
              </div>}
            </>)}
            {processing && settings.mode !== Mode.NoAI && <div className='bg-slate-200 p-2 rounded-lg w-[90%] ml-auto'>
              <Puff
                visible={true}
                height="25"
                width="25"
                color="grey"
                ariaLabel="puff-loading"
                wrapperStyle={{}}
                wrapperClass=""
              />
            </div>}
          </div>
          <div className='h-[150px] bg-blue-100 p-2 flex flex-row'>
            <textarea className='w-full outline-none px-1'
              value={input}
              onChange={(evt) => setInput(evt.target.value)}
            ></textarea>
            <div className='flex flex-col justify-center space-y-2'>
              <button className='outline-none text-2xl px-1 text-blue-600' title='Process'
                onClick={Process}
              ><RiSendPlane2Fill /></button>
              <button className='outline-none text-2xl px-1 text-red-600' title='Clear Messages'
                onClick={() => setMessages([])}
              ><MdOutlineClear /></button>
              <button className='outline-none text-2xl px-1 text-slate-600' title={getModeHelp()}
                onClick={() => setMessages([])}
              ><IoMdInformationCircleOutline /></button>
            </div>
          </div>
        </aside>
      </div>
      <footer className={"text-white flex h-[35px] items-center space-x-2 " + (processing ? 'bg-red-600' : 'bg-slate-900')}>
        <div className='bg-green-700 font-semibold h-full flex items-center'>Online</div>
        {/* <label className={'' + (processing ? '' : 'invisible')}>Proccessing ...</label> */}
        <div className='h-full flex items-center'>Mode: {settings.mode}</div>
        {/* {settings.mode === Mode.Assistant && <div className='h-full flex items-center space-x-2'>
          <div>ID:</div>
          <div className='bg-slate-400 text-black p-1'>123abc</div></div>} */}
      </footer>
    </>
  )
}

export default App2