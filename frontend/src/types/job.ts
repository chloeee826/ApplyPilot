export interface JobCreate {
  company_name: string
  title: string
  description: string
  location?: string | null
  source_url?: string | null
}

export interface Job extends JobCreate {
  id: string
  created_at: string
}
