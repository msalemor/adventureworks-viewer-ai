import { useEffect, useState } from "react"
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
import Markdown from "react-markdown";

const URL_BASE = import.meta.env.VITE_BASE_URL

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

const App = () => {
    // state
    const [settings, setSettings] = useState<ISettings>(Settings)
    const [processing, setProcessing] = useState(false)
    const [gridUpdating, setGridUpdating] = useState(false)
    const [gridColsRow, setGridColsRow] = useState<IGridColsRow>({ columns: [], rows: [] })
    const [sortColumns, setSortColumns] = useState<readonly SortColumn[]>([]);
    const [recordCounts, setRecordCounts] = useState<ICounts>(Counts)
    const [input, setInput] = useState<string>('')
    const [messages, setMessages] = useState<IMessage[]>([])
    const [assistantId, setAssistantId] = useState<string>('')
    const [openinfoarea, setOpeninfoarea] = useState(false)
    const [systemStatus, setSystemStatus] = useState({ status: 'Online', total: 2 })

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

    const fetchStatus = async () => {
        try {
            const response = await axios.get<{ status: string, total: number }>(URL_BASE + '/api/status');
            console.info(response.data)
            setSystemStatus(response.data)
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
        }
    };

    const refreshTime = 5000
    useEffect(() => {
        // Set up an interval to fetch data at regular intervals
        const comInterval = setInterval(fetchStatus, refreshTime);

        // Clean up the interval when the component unmounts
        return () => clearInterval(comInterval);
    }, [])

    // supporting functions
    const getGridDate = async (evt: any, target: string) => {
        evt.preventDefault();

        if (processing) return
        try {
            setProcessing(true)
            setGridUpdating(true)
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
            setGridUpdating(false)
        }
    }

    const getAssistantId = async () => {
        try {
            const resp = await axios.get<{ assistant_id: string }>(URL_BASE + '/api/assistant/id')
            setAssistantId(resp.data.assistant_id)
        } catch (error) {
            console.error(error)
        }
    }

    useEffect(() => {
        (async () => {
            await getAssistantId()
        })()
    }, [settings])

    const Process = async () => {
        if (processing) return
        setProcessing(true)

        try {
            const payload = { input: input }
            let URL = URL_BASE
            let msgs: IMessage[] = messages

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
                msgs.push({ role: msg.role, content: msg.content, imageUrl: null, mode: (msg.role === "assistant" ? settings.mode : null) })
                if ((settings.mode === Mode.SqlBot || settings.mode === Mode.MultiAgent) && msg.role === 'assistant') {
                    if (msg.rows) {
                        console.info(msg.rows)
                        if (msg.rows.length > 0) {
                            setGridColsRow({ columns: msg.columns, rows: msg.rows })
                            msgs.push({ role: 'assistant', content: 'Please check the grid for the answer', imageUrl: null, mode: Mode.SqlBot })
                        } else {
                            setGridColsRow({ columns: [], rows: [] })
                        }

                    }
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
                return '**Chatbot:** is connected to top customers and products. Examples:\n- Write a demand letter to the customer with the highest balance?\n- What are the top 5 products sold?'
            case Mode.SqlBot:
                return "**Sqlbot:** is connected to all tables including customers, top customers, products, top products, and orders. Examples:\n\n- What customers are in the United States?\n- What products have 'bike' in the description?"
            case Mode.Assistant:
                return '**Assistants API bot:** is connected to top customers and products.\Examples:\n- Create a chart of the sales by country.\n- What are the top 5 products sold?'
            case Mode.MultiAgent:
                return '**Multiagent bot:** is connected to top customers, products, weather, and shipping costs. Examples:\n- What are the top 5 products sold?\n- Write a query to find the customer with the highest balance.'
            default:
                return 'No AI mode'
        }
    }

    // type Comparator = (a: any, b: any) => number;
    // function getComparator(sortColumn: string): any {
    //     // switch (sortColumn) {
    //     //     case 'assignee':
    //     //     case 'title':
    //     //     case 'client':
    //     //     case 'area':
    //     //     case 'country':
    //     //     case 'contact':
    //     //     case 'transaction':
    //     //     case 'account':
    //     //     case 'version':
    //     //         return (a, b) => {
    //     //             return a[sortColumn].localeCompare(b[sortColumn]);
    //     //         };
    //     //     case 'available':
    //     //         return (a, b) => {
    //     //             return a[sortColumn] === b[sortColumn] ? 0 : a[sortColumn] ? 1 : -1;
    //     //         };
    //     //     case 'id':
    //     //     case 'progress':
    //     //     case 'startTimestamp':
    //     //     case 'endTimestamp':
    //     //     case 'budget':
    //     //         return (a, b) => {
    //     //             return a[sortColumn] - b[sortColumn];
    //     //         };
    //     //     default:
    //     //         throw new Error(`unsupported sortColumn: "${sortColumn}"`);
    //     // }
    //     const t = gridColsRow.rows[0][sortColumn]
    //     if (typeof t === 'number') {
    //         return (a: any, b: any): number => {
    //             return a[sortColumn] - b[sortColumn];
    //         };
    //     } else if (typeof t === 'boolean') {
    //         return (a: any, b: any): number => {
    //             return a[sortColumn] === b[sortColumn] ? 0 : a[sortColumn] ? 1 : -1;
    //         };
    //     } else if (typeof t === 'string' || t === undefined || t == null) {
    //         return (a: any, b: any): number => {
    //             //return a[sortColumn] === b[sortColumn] ? 0 : a[sortColumn] ? 1 : -1
    //             const ac = a[sortColumn] || ''
    //             const bc = b[sortColumn] || ''
    //             //return a[sortColumn] > (b[sortColumn]) ? 1 : -1
    //             return ac.localeCompare(bc);
    //         }
    //     }
    // }

    // const sortedRows = useMemo((): readonly any[] => {
    //     if (sortColumns.length === 0) return gridColsRow.rows;

    //     return [...gridColsRow.rows].sort((a, b) => {
    //         for (const sort of sortColumns) {
    //             const comparator = getComparator(sort.columnKey);
    //             const compResult = comparator(a, b);
    //             if (compResult !== 0) {
    //                 return sort.direction === 'ASC' ? compResult : -compResult;
    //             }
    //         }
    //         return 0;
    //     });
    // }, [gridColsRow.rows, sortColumns]);

    // JSX
    return (
        <>
            <header className="bg-slate-950 h-[40px] text-white p-2 flex items-center">
                <h1 className="text-xl font-bold">AdventureWorks Viewer</h1>
            </header>

            <div className="flex h-[calc(100vh-40px-26px)]">
                <main className={'bg-blue-100 ' + (settings.mode !== Mode.NoAI ? 'w-2/3' : 'w-full')}>
                    {/* select AI mode */}
                    <nav className="bg-slate-950 text-white flex items-center h-[40px] space-x-3 px-2">
                        <label className="font-semibold">Mode:</label>

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
                    {/* select grid information */}
                    <section className="bg-slate-900 h-[100px] flex space-x-2">
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
                    <section>
                        <DataGrid
                            sortColumns={sortColumns}
                            onSortColumnsChange={setSortColumns}
                            className='h-[calc(100vh-75px-35px-96px)]'
                            columns={gridColsRow.columns}
                            rows={gridColsRow.rows}
                            defaultColumnOptions={{
                                //sortable: true,
                                resizable: true
                            }}
                        />
                    </section>
                </main>
                <aside className={settings.mode !== Mode.NoAI ? 'w-1/3 flex flex-col' : 'hidden'}>
                    <div className={"bg-slate-950 text-white p-2 space-y-2 overflow-auto " + (openinfoarea ? "h-[calc(100vh-40px-36px-240px)]" : "h-[calc(100vh-40px-36px-140px)]")}>
                        {messages.map((msg, idx) => <>
                            {msg.role === 'user' && <div key={idx} className='bg-slate-700 p-2 rounded-lg w-[95%] ml-auto'>
                                {msg.content}
                            </div>}
                            {msg.role === 'assistant' && <div key={idx} className='bg-slate-800 text-white p-2 rounded-lg w-[95%] overflow-auto'>
                                <span className='font-semibold'>{msg.mode}: </span>
                                <Markdown>{msg.content}</Markdown></div>}
                            {msg.role === 'image' && <div>
                                <img key={idx} src={msg.content ? URL_BASE + msg.content : ""} alt='this is an image that was generated by Assistants API' />
                            </div>}
                        </>)}
                        {!gridUpdating && processing && settings.mode !== Mode.NoAI && <div className='bg-slate-700 p-2 rounded-lg w-[95%] ml-auto flex flex-col'>
                            <label>{input}</label>
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
                    {openinfoarea &&
                        <div id="infoarea" className="h-[100px] bg-yellow-100 text-black">
                            <div className="flex">
                                <div className="h-full overflow-auto">
                                    <Markdown className='w-full h-[100px] p-2'>{getModeHelp()}</Markdown>
                                </div>
                                <button className="px-1 outline-none top-9"
                                    onClick={() => setOpeninfoarea(false)}
                                ><MdOutlineClear /></button>
                            </div>

                        </div>}
                    <div className="flex bg-slate-900 p-2 h-[150px]">
                        <textarea className='w-full outline-none px-1 rounded-lg py-1'
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
                            <button className='outline-none text-2xl px-1 text-slate-300' title='Infomation and Samples'
                                onClick={() => setOpeninfoarea(true)}
                            ><IoMdInformationCircleOutline /></button>
                        </div>
                    </div>
                </aside>
            </div>
            <footer className={"text-white text-sm flex h-[26px] items-center " + (processing ? 'bg-red-600' : 'bg-slate-900')}>
                <div className={'font-semibold h-full flex items-center px-2 mr-1 ' + (systemStatus.total === 2 ? 'bg-green-700' : 'bg-orange-600')}>{systemStatus.status}</div>
                <div className='h-full flex items-center px-2 mr-1'>Mode:</div>
                <div className='h-full flex items-center px-1 bg-slate-300 text-black mr-1'>{settings.mode}</div>
                {(settings.mode === Mode.Assistant || settings.mode === Mode.MultiAgent) && <div className='h-full flex items-center px-1 bg-slate-300 text-black'>
                    <label className="font-semibold mr-1">ID:</label>
                    <label>{assistantId}</label></div>}

                {/* TODO: Add the assistant ID */}
                {/* TODO: Add butto to reset assistant ID */}
            </footer >
        </>
    )
}
export default App