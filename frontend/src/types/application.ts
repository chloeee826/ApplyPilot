export type ApplicationStatus =
  | 'saved'
  | 'applied'
  | 'interviewing'
  | 'offer'
  | 'rejected'
  | 'withdrawn'

export interface Application {
  id: string
  job_id: string
  status: ApplicationStatus
  created_at: string
  updated_at: string
}
