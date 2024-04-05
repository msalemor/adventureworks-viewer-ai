export enum Mode {
    NoAI = 'noai',
    Chatbot = 'chatbot',
    SqlBot = 'sqlbot',
    Assistant = 'assitant',
    MultiAgent = 'multiagent',
}

export interface ISettings {
    mode: Mode,
    max_token: string,
    temperature: string
}

export interface IResponse {
    role: string,
    user_name: string,
    user_id: string,
    content: string,
    columns: any[],
    rows: any[],
}

export interface IGridColsRow {
    columns: any[],
    rows: any[]
}

export interface ICounts {
    customers: number
    topCustomers: number
    products: number
    topProducts: number
    orderDetails: number
}

export interface IMessage {
    role: string
    content: string
    imageUrl: string | null
    mode: Mode | null
}