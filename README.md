# Adventureworks-AI-Viewer

A demo application to showcase adding intelligence to an application with different levels of complexity.

## Architecture

```mermaid
graph LR;
  A(user)<-->F(Frontend)
  F<-->B(Backend)
  B<-->O(GPTBot)
  B<-->Asst(Assistants API Bot)
  B<-->SQL(Sqbot)
  B<-->M(Multiagent Bot)
  M<-->O
  M<-->SQL
  M<-->Asst
```

## Requirements

### Database

- Deploy Azure SQL Database with Adventure Work to Azure
- Execute the scripts at: `src/backend/database/sql_views_script.sql` to add the supporting views

### Backend

- Python 3.11
- openai==1.16.1
- fastapi==0.110.1
- uvicorn[standard]==0.29.0
- pymssql==2.2.11
- pillow==10.3.0

### Frontend 

- React
- Tailwind CSS
- react-data-grid
- react-icons
- react-loader-spinner
- react-markdown
