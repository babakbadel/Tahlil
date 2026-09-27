import "./globals.css";
import type { Metadata } from "next";
export const metadata: Metadata={title:"Kamandar Intelligence | کماندار",description:"داشبورد مستقل هوش بازار کماندار"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="fa" dir="rtl"><body>{children}</body></html>}