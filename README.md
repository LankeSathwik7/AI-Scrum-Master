# 🤖 Scrum AI Assistant

An AI-powered Scrum automation toolkit for managing Agile workflows, featuring Slack integration, Trello synchronization, risk prediction, and task prioritization.

## 📋 Overview

This system provides a collection of tools to help Agile teams streamline their Scrum processes:

- **🤖 AI Scrum Master Bot**: Facilitates daily standups, tracks blockers, and creates tickets
- **📊 Trello Integration**: Creates cards from blockers, archives old cards, and syncs project data
- **🧠 Sentiment Analysis**: Analyzes retrospective feedback to identify team sentiment
- **📈 Prediction Framework**: Forecasts project risks and recommends actions
- **📑 Task Prioritization**: Auto-prioritizes work items based on configurable rules
- **📱 Interactive Dashboard**: Streamlit-based visualization of team metrics and insights

## 🏗️ Architecture

```
├── LICENSE
├── README.md
├── bots
│   ├── __init__.py
│   ├── retrospective.py
│   ├── slack_bot.py
│   ├── slack_standup_bot.py
│   └── trello_integration.py
├── core
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   ├── security.py
│   └── utils.py
├── models
│   ├── __init__.py
│   ├── risk_predictor.py
│   └── task_prioritizer.py
├── report_generator.py
├── requirements.txt
├── scrum_ai.log
├── slack_bot.log
├── sprints.db
├── standup_bot.log
├── tests
│   ├── __init__.py
│   ├── test_dashboard.py
│   └── test_data.py
└── ui
    ├── __init__.py
    ├── assets
    │   └── __init__.py
    └── dashboard.py
```

## ✨ Features

### 💬 Slack Bot Integration

- Automated daily standup reminders and facilitation
- Detects blockers in team messages
- Creates Trello cards for identified blockers
- Supports Socket Mode for secure communication

### 📋 Trello Integration

- Fetches board data for analysis
- Creates cards for blockers detected in Slack
- Archives old cards automatically
- Manages board organization

### 📊 Retrospective Analysis

- Sentiment analysis of team retrospective discussions
- Uses RoBERTa model for advanced NLP processing
- Detects positive, negative, and neutral sentiment
- Provides quantitative data on team morale

### 🔮 Risk Prediction

- Uses Prophet forecasting model to predict sprint completion
- Identifies high-risk periods during sprints
- Suggests mitigation strategies based on risk level
- Provides visualizations of risk factors

### 📝 Task Prioritization

- ML-based prioritization of backlog items
- Considers due dates, dependencies, and team capacity
- Auto-adjusts as new information becomes available
- Provides explainable priority scores

### 📲 Interactive Dashboard

- Real-time visualization of team metrics
- Blocker tracking and highlighting
- Sentiment analysis results
- Sprint burndown with risk prediction
- Team capacity planning

### 🗄️ Database Management

- SQLite database with migration support
- Tracks predictions, tasks, team capacity and retrospectives
- Version control for schema changes
- Safe transaction handling

### 🚀 Deployment Pipeline

- GitHub Actions workflow for CI/CD
- Daily automated runs on schedule
- Caches dependencies for faster execution
- Automatic deployment to Streamlit

## ⚙️ Configuration

The application uses environment variables for configuration. Create a `.env` file with:

```
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
SLACK_TEAM_CHANNEL=general
SLACK_RETRO_CHANNEL=retrospective

# Trello Configuration
TRELLO_API_KEY=...
TRELLO_TOKEN=...
TRELLO_BOARD_ID=...
TRELLO_LIST_ID=...
TRELLO_ARCHIVE_LIST=...

# Application Settings
RISK_THRESHOLD=10
POSITIVE_THRESHOLD=0.25
CRITICAL_THRESHOLD=0.15
```

## 🛠️ Installation

1. Clone the repository
   ```bash
   git clone https://github.com/LankeSathwik7/AI-Scrum-Master.git
   cd AI-Scrum-Master
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Initialize the database
   ```bash
   python core/database.py
   ```

5. Run a bot
   ```bash
   python bots/slack_bot.py
   ```

6. Launch the dashboard
   ```bash
   streamlit run ui/dashboard.py
   ```

## 💻 Technical Requirements

- Python 3.10+
- Required packages (from requirements.txt):
  - slack-bolt==1.18.0
  - spacy==3.7.2
  - python-dotenv==1.0.0
  - requests==2.31.0
  - scikit-learn==1.3.2
  - streamlit==1.28.0
  - plotly==5.18.0
  - pandas==2.0.3
  - streamlit-autorefresh==1.0.1
  - slack-sdk==3.23.0
  - transformers[torch]==4.36.2
  - prophet==1.1.5
  - accelerate==0.27.2
  - tabulate==0.9.0
  - flask-limiter
  - python-dotenv-vault
  - huggingface_hub[hf_xet]
  - python-dateutil

## 🔄 Pipeline Workflow

The GitHub Actions workflow runs daily and:

1. Sets up Python environment
2. Caches dependencies
3. Runs database migrations
4. Executes risk prediction model
5. Prioritizes tasks
6. Runs tests
7. Deploys to Streamlit dashboard

**Note:** GitHub Actions have been disabled in this repository. The workflow file (`.github/workflows/main.yml`) is retained for reference only.

## 🔒 Security Features

- Rate limiting for API endpoints
- Environment variable encryption support
- OAuth integration for Trello
- Proper error handling and logging
- Input validation and sanitization

## 🧪 Development

### Running Tests

```bash
pytest tests/
```

### Adding New Features

1. Create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Implement your changes
3. Add tests for your feature
4. Run tests to ensure everything passes
5. Create a pull request

## ❓ Troubleshooting

### Common Issues

- **Slack API connection errors**: Verify your token permissions and ensure Socket Mode is enabled
- **Database migration failures**: Check the SQLite file permissions
- **Prediction model errors**: Ensure you have enough historical data for accurate predictions
- **Dashboard rendering issues**: Verify Streamlit version compatibility

### Logs

Log files are stored in the project root:
- `scrum_ai.log` - Main application logs
- `slack_bot.log` - Slack bot interaction logs
- `standup_bot.log` - Standup facilitation logs

## 🔮 Future Enhancements

- Integration with GitHub/GitLab for code metrics
- Enhanced ML models for better risk prediction
- Mobile companion app
- Meeting summarization features
- Team performance analytics

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgements

- Special thanks to the open-source community for the amazing libraries that make this possible