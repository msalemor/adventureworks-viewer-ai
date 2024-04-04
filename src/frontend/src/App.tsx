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
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
// import './App.css'

const URL_BASE = 'http://127.0.0.1:8000'
//const URL_BASE: string = window.location.protocol + "//" + window.location.host
//const URL_BASE = ''

enum Mode {
  NoAI = 'noai',
  Chatbot = 'chatbot',
  SqlBot = 'sqlbot',
  Assistant = 'assitant',
  MultiAgent = 'multiagent',
}

interface ISettings {
  mode: Mode,
  max_token: string,
  temperature: string
}

// {'role':'assistant','user_name':user_name,'user_id':user_id,'content':content,'columns':columns,'rows':rows}
interface IResponse {
  role: string,
  user_name: string,
  user_id: string,
  content: string,
  columns: any[],
  rows: any[],
}

const Settings = {
  mode: Mode.Chatbot,
  max_token: '500',
  temperature: '0.3',
}
interface IGridColsRow {
  columns: any[],
  rows: any[]
}

const Counts = {
  customers: { count: 0 },
  topCustomers: { count: 0 },
  products: { count: 0 },
  topProducts: { count: 0 },
  orderDetails: { count: 0 }
}

interface ICount {
  count: number
}
interface ICounts {
  customers: ICount
  topCustomers: ICount
  products: ICount
  topProducts: ICount
  orderDetails: ICount
}

interface IMessage {
  role: string
  content: string
  imageUrl: string | null
  mode: Mode | null
}

function App() {
  const [settings, setSettings] = useState<ISettings>(Settings)
  const [processing, setProcessing] = useState(false)
  const [gridColsRow, setGridColsRow] = useState<IGridColsRow>({ columns: [], rows: [] })
  const [sortColumns, setSortColumns] = useState<readonly SortColumn[]>([]);
  const [recordCounts, setRecordCounts] = useState<ICounts>(Counts)
  const [input, setInput] = useState<string>('')
  const [messages, setMessages] = useState<IMessage[]>([])

  useEffect(() => {
    fetch(URL_BASE + '/api/counts')
      .then(resp => resp.json())
      .then(data => {
        setRecordCounts({ customers: data.customers, topCustomers: data.topCustomers, products: data.products, topProducts: data.topProducts, orderDetails: data.orderDetails })
      })
  }, [])

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
      // axios.post(URL_BASE + 'api/process', { input: input })
      //   .then(resp => {
      //     console.log(resp.data)
      //     setMessages([...messages, { role: 'user', content: input, imageUrl: null }])
      //     setMessages([...messages, { role: 'assistant', content: resp.data, imageUrl: null }])
      //   })
      //alert('Processing')
      const payload = { input: input }
      let msgs = messages
      //setMessages([...messages, ...{ role: 'user', content: input, imageUrl: null }])
      let URL = URL_BASE
      let resp: any = null

      if (settings.mode === Mode.Chatbot) {
        msgs.push({ role: 'user', content: input, imageUrl: null, mode: null })
        setMessages(msgs)
        URL += '/api/chatbot'
        resp = await axios.post<IResponse>(URL, payload)
        let data = resp.data
        msgs.push({ role: 'assistant', content: data.content, imageUrl: null, mode: settings.mode })
        setMessages(msgs)
      } else if (settings.mode === Mode.SqlBot) {
        msgs.push({ role: 'user', content: input, imageUrl: null, mode: null })
        setMessages(msgs)
        URL += '/api/sqlbot'
        resp = await axios.post<IResponse>(URL, payload)
        const data = resp.data
        msgs.push({ role: 'assistant', content: data.content, imageUrl: null, mode: settings.mode })
        setMessages(msgs)
        setGridColsRow({ columns: data.columns, rows: data.rows })
        if (data.rows && data.rows.length > 0) {
          msgs.push({ role: 'assistant', content: "Please check the grid for the answer.", imageUrl: null, mode: settings.mode })
          setMessages(msgs)
        }
      } if (settings.mode === Mode.Assistant) {
        URL += '/api/assistants'
        resp = await axios.post<IResponse[]>(URL, payload)
        const data = resp.data
        data.forEach((msg: IResponse) => {
          msgs.push({ role: msg.role, content: msg.content, imageUrl: null, mode: (msg.role === "assistant" ? settings.mode : null) })
        })
      }

    }
    catch (error) {
      console.error(error)
    }
    finally {
      setInput('')
      setProcessing(false)
    }
  }

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
      <section className='h-[100px] flex space-x-1 bg-slate-900'>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer'
          onClick={(evt) => getGridDate(evt, 'customers')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.customers.count}</label>
          <label className='font-semibold uppercase text-3xl'><BsPersonFill title='Customers' /></label>
        </div>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer'
          onClick={(evt) => getGridDate(evt, 'sales')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.topCustomers.count}</label>
          <label className='font-semibold uppercas text-3xl'><BsPersonFillUp title='Top Customers' /></label>
        </div>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer'
          onClick={(evt) => getGridDate(evt, 'products')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.products.count}</label>
          <label className='font-semibold uppercase text-3xl'><RiProductHuntLine title='Products' /></label>
        </div>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer'
          onClick={(evt) => getGridDate(evt, 'sold')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.topProducts.count}</label>
          <label className='font-semibold uppercase text-3xl'><RiProductHuntFill title='Top Products' /></label>
        </div>
        <div className='space-y-2 w-[120px] bg-blue-600 text-white flex flex-col p-2 items-center justify-center hover:cursor-pointer'
          onClick={(evt) => getGridDate(evt, 'orders')}
        >
          <label className='bg-white text-blue-600 rounded-xl px-1'>{recordCounts.orderDetails.count}</label>
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
        <aside className={(settings.mode == Mode.NoAI ? 'invisible' : 'md:w-1/3 flex flex-col')}>
          <div className='h-[calc(100vh-75px-35px-100px-150px)] flex flex-col overflow-auto p-2 space-y-2'>
            {messages.map((msg) => <>
              {msg.role === 'user' && <div className='bg-slate-200 p-2 rounded-lg w-[90%] ml-auto'>
                {msg.content}
              </div>}
              {msg.role === 'assistant' && <div className='bg-slate-300 p-2 rounded-lg w-[90%]'>
                <span className='font-semibold'>{msg.mode}: </span>{msg.content}</div>}
              {msg.role === 'image' && <div>
                <img src={msg.content ? URL_BASE + msg.content : ""} alt='this is an image that was generated by Assistants API' />
              </div>}
            </>)}
            {processing && <div className='bg-slate-200 p-2 rounded-lg w-[90%] ml-auto'>
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
            <button className='outline-none text-2xl px-1 text-blue-600' title='Send Message'
              onClick={Process}
            ><RiSendPlane2Fill /></button>
            <button className='outline-none text-2xl px-1 text-red-600' title='Clear Messages'
              onClick={() => setMessages([])}
            ><MdOutlineClear /></button>
          </div>
        </aside>
      </div>
      <footer className={"text-white flex h-[35px] items-center space-x-2 " + (processing ? 'bg-red-600' : 'bg-slate-900')}>
        <label className='bg-green-700 p-1'>Online</label>
        <label className={'' + (processing ? '' : 'invisible')}>Proccessing ...</label>
      </footer>
    </>
  )
}

export default App
