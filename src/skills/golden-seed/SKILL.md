---
name: golden-seed
description: When users are ready to log in to the AI Golden Seed (or Golden Seed) website and perform tasks, they can complete the corresponding tasks by following the workflow below
---

# Golden Seed Skill

## Workflow Checklist

Copy and track progress:
```
Golden Seed Skill Use Progress:
- [ ] Step 1: Navigate and login to AI Golden Seed
```

## Step 1: Navigate and Login to AI Golden Seed

### 1.1 Navigate to Login Page

The login URL is:
```
https://192.168.103.90:8082/login?redirect=/index
```

**IMPORTANT:** This URL uses a self-signed SSL certificate. You must use `browser_run_code` with CDP (Chrome DevTools Protocol) to bypass the certificate error.

**DO NOT use `browser_navigate`** - it will fail with `ERR_CERT_COMMON_NAME_INVALID`.

Instead, use this code:

```javascript
async (page) => {
  const client = await page.context().newCDPSession(page);
  await client.send('Security.setIgnoreCertificateErrors', { ignore: true });
  await page.goto('https://192.168.103.90:8082/login?redirect=/index');
  await page.waitForLoadState('domcontentloaded');
  return 'Navigated to login page';
}
```

**Tool to use:** `browser_run_code`

### 1.2 Take Snapshot and Identify Login Form

After navigation, use `browser_snapshot` to see the page structure.

**Expected page elements:**
- **Heading**: "若依后台管理系统" (RuoYi Backend Management System)
- **Username textbox**: label "账号" (Account)
- **Password textbox**: label "密码" (Password)
- **Login button**: text "登 录" (Login)
- **Remember password checkbox**: label "记住密码"

**Example field references** (these may change, always verify with snapshot):
- Username textbox: ref=e13
- Password textbox: ref=e21
- Login button: ref=e28

### 1.3 Request Credentials from User

**IMPORTANT:** Always ask the user for credentials. Never hardcode them in the skill.

Ask the user:
```
Please provide your AI Golden Seed login credentials:
- Username/账号: ?
- Password/密码: ?
```

### 1.4 Fill in Login Form

Use `browser_type` to fill in each field:

**Step 1: Fill username**
```yaml
browser_type:
  element: "Username/账号 textbox"
  ref: <username ref from snapshot>
  text: "<user-provided username>"
```

**Step 2: Fill password**
```yaml
browser_type:
  element: "Password/密码 textbox"
  ref: <password ref from snapshot>
  text: "<user-provided password>"
```

**Note:** Use the refs from your snapshot. The example refs (e13, e21) may change.

### 1.5 Submit Login

Click the login button:

```yaml
browser_click:
  element: "Login button (登 录)"
  ref: <login button ref from snapshot>
```

### 1.6 Verify Successful Login

After clicking, verify success by checking:

1. **URL change**: Should redirect to `/index`
2. **Page title**: Should still be "万家乐后台管理系统"
3. **Console logs**: Look for:
   - `[Auth] ✅ localStorage存储成功` (Token saved)
   - `[响应拦截] /login 状态码: 200` (Login success)
   - `[UserStore] ✅ 用户信息存储完成` (User info saved)
4. **Take a snapshot** to confirm you see:
   - Navigation menu bar
   - Breadcrumb with "首页" (Home)
   - User avatar/profile

**If login fails:**
- Check console logs for error messages
- Verify credentials were correct
- Look for CAPTCHA requirements
- Ask user to verify credentials

### 1.7 Post-Login State

After successful login:
- **Token is stored**: Available in localStorage for API calls
- **User is authenticated**: Can access protected pages
- **Ready for next steps**: The skill can now proceed to perform user's requested tasks on the platform

**Common login success indicators:**
```
URL: https://192.168.103.90:8082/index
Logs show:
- /login 状态码: 200, 业务code: 200
- Token saved (length 184)
- User roles: ["ai_main_page_manager", ...]
- Permissions loaded successfully
```

---

Once logged in successfully, the skill can proceed to perform the user's requested tasks on the AI Golden Seed platform.
