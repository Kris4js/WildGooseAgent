BROWSER_AUTOMATION_DESCRIPTION: str = """
Automated browser interaction using Playwright for web scraping, form filling, and authentication flows.

## When to Use

- **Authentication & Login**: Multi-step login flows, OAuth/SSO, form-based authentication
- **Web Scraping**: Extract data from websites that require JavaScript rendering
- **Form Operations**: Fill out and submit web forms, file uploads, dropdown selections
- **Interactive Tasks**: Click buttons, navigate menus, hover over elements, keyboard input
- **Session Management**: Maintain authentication state across multiple operations
- **Visual Verification**: Take screenshots, capture accessibility snapshots for debugging
- **Dynamic Content**: Access content that loads via JavaScript or requires user interaction
- **Internal Applications**: Access internal dashboards behind self-signed SSL certificates

## When NOT to Use

- Simple API data retrieval (use HTTP requests or web_search instead)
- Static HTML scraping without JavaScript (use simpler tools like BeautifulSoup)
- Public websites with simple GET requests (use web_search or direct HTTP)
- Large-scale data extraction (browser automation is resource-intensive)
- Real-time streaming data (use WebSocket or API connections)

## Capabilities

### Navigation & Inspection
- Navigate to URLs with SSL certificate bypass support
- Capture accessibility snapshots (better than screenshots for understanding page structure)
- Take screenshots for visual verification
- Monitor console logs and network requests
- Manage multiple browser tabs

### Element Interaction
- Click buttons, links, and interactive elements
- Type text into input fields
- Hover over elements to trigger dropdowns or tooltips
- Press keyboard keys (Enter, Tab, arrow keys, etc.)
- Select dropdown options
- Drag and drop elements

### Form Operations
- Fill multiple form fields at once
- Handle checkboxes and radio buttons
- Upload files
- Handle JavaScript alerts and confirmation dialogs

### Session Management
- Save and restore browser sessions (cookies, localStorage)
- Create isolated browser contexts for different tasks
- Reuse authentication across multiple operations
- Handle multi-step authentication flows

### Advanced Operations
- Execute custom JavaScript in page context
- Wait for elements to appear or specific conditions
- Handle dynamic content loading
- Bypass SSL certificate errors for internal applications

## Usage Notes

- **Session Persistence**: Use session IDs to maintain login state across multiple operations
- **SSL Errors**: Internal sites with self-signed certificates require special handling via CDP
- **Element Selection**: Uses accessibility tree snapshots for robust element identification
- **Timeouts**: Configure appropriate timeouts for page loads and element waiting
- **Resource Management**: Browser sessions are automatically cleaned up after use
- **Error Handling**: Includes retry logic for transient failures like network timeouts

## Best Practices

1. **Use Snapshots First**: Always take a snapshot before interacting to understand page structure
2. **Verify References**: Element references (e.g., ref=e13) change - always get fresh snapshots
3. **Session Reuse**: For multi-step tasks, use session IDs to maintain authentication state
4. **Wait for Loads**: Use wait_for operations to ensure pages/elements are ready
5. **Handle Errors Gracefully**: Check snapshots for error messages, CAPTCHAs, or redirects
6. **Clean Up Sessions**: Close browser sessions when done to free resources

## Tool Categories

### Navigation Tools
- `browser_navigate` - Navigate to URL
- `browser_snapshot` - Get accessibility tree snapshot
- `browser_take_screenshot` - Capture visual screenshot
- `browser_tabs` - Manage browser tabs (list, new, close, select)
- `browser_navigate_back` - Go back to previous page

### Interaction Tools
- `browser_click` - Click on elements
- `browser_type` - Type text into form fields
- `browser_hover` - Hover over elements
- `browser_press_key` - Press keyboard keys
- `browser_select_option` - Select dropdown options
- `browser_drag` - Drag and drop elements

### Form Tools
- `browser_fill_form` - Fill multiple form fields at once
- `browser_file_upload` - Upload files
- `browser_handle_dialog` - Handle alert/confirm dialogs

### Inspection Tools
- `browser_console_messages` - Get console logs
- `browser_network_requests` - Get network activity
- `browser_evaluate` - Execute JavaScript

### Waiting Tools
- `browser_wait_for` - Wait for text/elements/timeout
- `browser_resize` - Resize browser window

### Session Tools
- `browser_close` - Close browser/session

## Example Use Cases

### Login Flow
1. Navigate to login page (handle SSL if needed)
2. Take snapshot to identify form fields
3. Fill in username and password
4. Click login button
5. Verify successful login via URL change or user profile visible

### Data Extraction
1. Navigate to target page
2. Take snapshot to understand structure
3. Click required buttons or fill search forms
4. Take screenshots or snapshots of results
5. Extract data from accessibility tree

### Multi-Step Workflows
1. Create session with ID
2. Navigate and login
3. Perform multiple operations using same session ID
4. Close session when complete

## Security Considerations

- **Credentials**: Never hardcode credentials - ask user at runtime
- **Session Storage**: Sessions store cookies/tokens - clear after use
- **File Uploads**: Restrict to specific paths for security
- **JavaScript Execution**: Limit scope and validate inputs
- **Internal Sites**: Use CDP SSL bypass only for trusted internal applications
""".strip()
