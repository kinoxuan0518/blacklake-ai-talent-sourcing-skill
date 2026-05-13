# Configuration

All secrets and machine-specific values must come from environment variables.

## Tracking Table

Required:

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_APP_TOKEN`
- `FEISHU_TABLE_ID`

Optional:

- `FEISHU_BASE_URL`, default `https://open.feishu.cn/open-apis`

Expected fields:

- `姓名`
- `邮箱`
- `机构`
- `方向`
- `代表工作`
- `评级`
- `来源`
- `邮件主题`
- `草稿状态`
- `发送状态`
- `回复状态`
- `发现日期`
- `备注`

## Mail Drafts

Required:

- `ALIMAIL_USER_EMAIL`
- `ALIMAIL_USER_NAME`
- `ALIMAIL_REFRESH_TOKEN_KEY`, default `RefreshToken`

Optional:

- `ALIMAIL_CLIENT_ID`, default `alimail_standard_redcoast_mac`
- `ALIMAIL_TOKEN_URL`, default `https://mailsso.mxhichina.com/oauth2/v2.0/token.json`
- `ALIMAIL_WEBMAIL_BASE`, default `https://qiye.aliyun.com/alimail/`
- `ALIMAIL_APPDATA_ROOT`, default `~/Library/Application Support/alimail-standard/appdata`
- `ALIMAIL_DRAFT_FOLDER_ID`, default `5`
- `ALIMAIL_SENT_FOLDER_ID`, default `1`

Local database paths are derived from `ALIMAIL_APPDATA_ROOT` and `ALIMAIL_USER_EMAIL`.

## Privacy Checklist Before Publishing

Run a scan for:

- Real app tokens, app secrets, access tokens, refresh tokens, and GitHub tokens.
- Real personal or company email addresses.
- Absolute local paths with usernames.
- Candidate names and private outreach history.
- Company-specific table ids unless the repository is private and approved.
