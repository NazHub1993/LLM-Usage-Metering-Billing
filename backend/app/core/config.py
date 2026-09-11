from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url:str
    supabase_anon_key:str
    supabase_service_role_key:str
    stripe_secret_key:str
    stripe_pro_price_id:str
    stripe_webhook_secret:str

    class Config:
        env_file=".env"

settings=Settings()