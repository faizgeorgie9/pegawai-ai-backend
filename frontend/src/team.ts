// The working team, as the backend names them (roles and badges come from real responses).
// The response's `color` field picks the person's pale tint; `avatar` is an emoji and is not shown,
// each person gets their initial instead.
import type { Department } from './api'

export type Hue = 'amber' | 'teal' | 'blue' | 'sky' | 'plain'
export interface Member {
  name: string
  role: string
  makes: string
}

// response colour name -> tint family ("indigo" is drawn as a pale blue; the product has no indigo)
export function hueOf(color?: string): Hue {
  switch (color) {
    case 'amber':
      return 'amber'
    case 'teal':
      return 'teal'
    case 'indigo':
      return 'blue'
    case 'sky':
      return 'sky'
    default:
      return 'plain'
  }
}

export const TEAMS: Record<Department, { label: string; blurb: string; members: (Member & { color: string })[] }> = {
  marketing: {
    label: 'Marketing',
    blurb: 'Naskah, penilaian mutu, dan visual dalam satu draf.',
    members: [
      { name: 'Rian', role: 'Copywriting Specialist', makes: 'Naskah AIDA', color: 'amber' },
      { name: 'Diana', role: 'Creative Director & QC Auditor', makes: 'Skor QC', color: 'teal' },
      { name: 'Budi', role: 'Visual Designer & Art Director', makes: 'Aset Visual & Prompt', color: 'indigo' },
    ],
  },
  customer_support: {
    label: 'Customer Service',
    blurb: 'Balasan untuk pelanggan, lengkap dengan audit mutunya.',
    members: [
      { name: 'Siti', role: 'Frontline Support Specialist', makes: 'Customer Response', color: 'sky' },
      { name: 'Hendra', role: 'CS Team Lead & Quality Auditor', makes: 'Audit QA', color: 'teal' },
    ],
  },
}

export const EXAMPLES: Record<Department, { title: string; text: string }[]> = {
  marketing: [
    {
      title: 'Posting LinkedIn: otomasi balasan chat',
      text: 'Buat posting LinkedIn untuk pemilik UMKM tentang cara otomasi balasan chat menghemat waktu admin. Nada membumi, tanpa klaim berlebihan, akhiri dengan ajakan audit alur kerja gratis.',
    },
    {
      title: 'Caption Instagram: kampanye Desember',
      text: 'Buat caption Instagram untuk kampanye Desember jasa Pegawai AI. Sasarannya toko online kecil yang kewalahan membalas chat saat musim belanja akhir tahun.',
    },
  ],
  customer_support: [
    {
      title: 'TKT-1002: laporan mingguan tidak muncul',
      text: 'Tiket TKT-1002: pelanggan Ibu Rina melaporkan laporan mingguan di dashboard tidak muncul sejak kemarin. Buat draf balasan yang empatik dengan langkah pengecekan bertahap.',
    },
    {
      title: 'TKT-1003: layanan terputus dan minta refund',
      text: 'Tiket TKT-1003: pelanggan Pak Andi marah karena layanan terputus dua hari, meminta refund penuh, dan mengancam akan membawa masalah ini ke jalur hukum. Buat draf balasan dan beri rekomendasi eskalasinya.',
    },
    {
      title: 'TKT-1004: tagihan ganda dan minta refund',
      text: 'Tiket TKT-1004 (data sintetis): pelanggan Ibu Sari menemukan tagihan langganan bulan ini terpotong dua kali dengan jumlah sama dan meminta pengembalian dana untuk satu tagihan. Buat draf balasan berdasarkan data terverifikasi dan rekomendasikan apakah perlu eskalasi, tanpa menyatakan refund sudah diproses.',
    },
  ],
}

// SOP minimum QC score per department. Only Marketing has one; Customer Service has none on record.
export const MIN_SCORE: Partial<Record<Department, number>> = { marketing: 85 }
