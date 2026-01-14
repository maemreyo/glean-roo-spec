# Roo Custom Tools: Tính Năng, Cấu Hình và Ví Dụ Sử Dụng

## Giới Thiệu Tổng Quan về Roo Custom Tools

Roo Custom Tools là một tính năng thử nghiệm của Roo Code — một công cụ AI hỗ trợ lập trình mã nguồn mở — cho phép người dùng định nghĩa các công cụ tùy chỉnh bằng TypeScript hoặc JavaScript để AI có thể gọi và sử dụng giống như các công cụ có sẵn. Thay vì phải nhắc đi nhắc lại các bước quy trình giống nhau cho mỗi tác vụ, bạn có thể chuẩn hóa các thao tác đặc thù của dự án thành các công cụ riêng, giúp tối ưu hóa quy trình làm việc của nhóm và đảm bảo tính nhất quán trong quá trình phát triển. Tính năng này đặc biệt hữu ích cho các dự án có quy trình phức tạp, yêu cầu thực hiện nhiều bước lặp đi lặp lại hoặc cần tích hợp với các hệ thống nội bộ của dự án. Khi được kích hoạt, các custom tools sẽ được tự động phê duyệt, nghĩa là Roo sẽ không hỏi xin phép trước khi thực thi chúng, điều này giúp tăng tốc độ làm việc nhưng cũng đòi hỏi người dùng phải cẩn thận khi viết và cấu hình các công cụ tùy chỉnh.

Điểm khác biệt quan trọng giữa Custom Tools và MCP (Model Context Protocol) nằm ở mục đích sử dụng: trong khi MCP được thiết kế để tích hợp với các dịch vụ bên ngoài như tìm kiếm, API và các công cụ bên thứ ba, thì Custom Tools lại nhẹ hơn và phù hợp hơn cho logic nội bộ của dự án — những thao tác đặc thù mà chỉ dự án của bạn mới cần. Điều này giúp bạn dễ dàng tạo ra các công cụ chuyên biệt mà không cần phải cấu hình phức tạp như MCP. Custom Tools sử dụng Zod để xác thực tham số đầu vào và tự động chuyển đổi từ TypeScript, giúp đảm bảo tính an toàn về kiểu dữ liệu và giảm thiểu lỗi trong quá trình phát triển.

## Cấu Trúc và Thành Phần Của Custom Tools

### Vị Trí Lưu Trữ Công Cụ

Roo Code hỗ trợ hai vị trí để lưu trữ custom tools, cho phép bạn linh hoạt trong việc quản lý và chia sẻ công cụ giữa các dự án. Thư mục `.roo/tools/` trong thư mục gốc của dự án được sử dụng để lưu trữ các công cụ đặc thù cho từng dự án riêng lẻ, đảm bảo rằng mỗi dự án có thể có bộ công cụ riêng phù hợp với yêu cầu và quy trình của mình. Trong khi đó, thư mục `~/.roo/tools/` ở cấp độ toàn cục cho phép bạn tạo các công cụ chung có thể được sử dụng trong nhiều dự án khác nhau, tiết kiệm thời gian và công sức khi làm việc trên nhiều dự án có quy trình tương tự. Khi có sự xung đột tên giữa công cụ toàn cục và công cụ dự án, Roo Code sẽ ưu tiên sử dụng công cụ dự án, cho phép bạn ghi đè hành vi của công cụ toàn cục khi cần thiết.

Việc phân biệt giữa công cụ toàn cục và công cụ dự án giúp tổ chức quy trình làm việc một cách hiệu quả. Các công cụ toàn cục thường bao gồm các tiện ích chung như gửi thông báo, tích hợp với hệ thống CI/CD hoặc các hàm tiện ích được sử dụng thường xuyên. Trong khi đó, công cụ dự án thường chứa các logic nghiệp vụ đặc thù như tạo template code theo chuẩn của dự án, kiểm tra tuân thủ coding standards hoặc tự động hóa các bước deploy riêng của dự án. Cách tiếp cận này giúp duy trì tính module và khả năng bảo trì mã nguồn trong dài hạn.

### Cấu Trúc Cơ Bản Của Một Custom Tool

Mỗi custom tool được định nghĩa thông qua hàm `defineCustomTool` từ package `@roo-code/types`, với bốn thành phần chính cần được chỉ định rõ ràng. Thuộc tính `name` xác định tên của công cụ mà AI sẽ nhìn thấy và sử dụng, do đó cần đặt tên ngắn gọn, rõ ràng và phản ánh đúng chức năng của công cụ. Thuộc tính `description` mô tả công cụ làm gì và được hiển thị cho AI, giúp AI hiểu khi nào nên gọi công cụ này — một mô tả tốt sẽ giúp AI đưa ra quyết định chính xác hơn về việc sử dụng công cụ. Thuộc tính `parameters` định nghĩa các tham số đầu vào thông qua schema Zod, tự động chuyển đổi thành JSON Schema để xác thực và hiển thị cho AI biết công cụ cần những tham số nào. Cuối cùng, hàm `execute` là async function thực hiện logic của công cụ và trả về kết quả dưới dạng string.

```typescript
import { parametersSchema as z, defineCustomTool } from "@roo-code/types"

export default defineCustomTool({
  name: "tool_name",
  description: "What the tool does (shown to AI)",
  parameters: z.object({
    param1: z.string().describe("Parameter description"),
    param2: z.number().describe("Another parameter"),
  }),
  async execute(args, context) {
    // args are type-safe and validated
    // context provides: mode, task
    return "Result string shown to AI"
  }
})
```

Context được truyền vào hàm execute cung cấp thông tin về mode hiện tại và task đang thực hiện, cho phép công cụ tùy chỉnh hành vi dựa trên ngữ cảnh. Điều này đặc biệt hữu ích khi bạn muốn công cụ có hành vi khác nhau tùy thuộc vào chế độ làm việc hoặc loại tác vụ đang được thực hiện. Ví dụ, một công cụ tạo log có thể ghi log chi tiết hơn ở chế độ debug và chỉ ghi log cơ bản ở chế độ production.

## Hướng Dẫn Kích Hoạt và Cấu Hình

### Bật Tính Năng Experimental

Để sử dụng Custom Tools, trước tiên bạn cần kích hoạt tính năng thử nghiệm này trong Roo Code. Quy trình kích hoạt bao gồm việc mở cài đặt Roo Code bằng cách nhấp vào biểu tượng bánh răng (⚙) ở góc trên bên phải của giao diện, sau đó điều hướng đến tab "Experimental" hoặc "Advanced Settings" tùy thuộc vào phiên bản bạn đang sử dụng. Trong phần "Experimental Features", bạn sẽ tìm thấy tùy chọn "Enable custom tools" — hãy bật công tắc này để kích hoạt tính năng. Lưu ý rằng đây là tính năng thử nghiệm, có thể không ổn định và có thể thay đổi đáng kể trong các phiên bản tương lai, vì vậy hãy cân nhắc kỹ trước khi sử dụng trong môi trường production.

Một điểm quan trọng cần lưu ý là khi Custom Tools được bật, tất cả các công cụ tùy chỉnh sẽ được tự động phê duyệt — Roo sẽ không hỏi xin phép trước khi thực thi chúng. Điều này có nghĩa là nếu bạn định nghĩa một công cụ có chứa logic nguy hiểm như xóa file hay thực thi lệnh hệ thống, AI có thể vô tình kích hoạt chúng mà không có cảnh báo. Vì vậy, bạn nên review kỹ các công cụ tùy chỉnh trước khi thêm vào và chỉ định nghĩa các công cụ từ nguồn đáng tin cậy.

### Cài Đặt npm Dependencies

Custom Tools hỗ trợ sử dụng các thư viện npm, cho phép bạn tận dụng hệ sinh thái JavaScript phong phú để xây dựng các công cụ mạnh mẽ. Để cài đặt dependencies, bạn cần di chuyển đến thư mục chứa tools và khởi tạo npm project. Quy trình bao gồm các bước: đầu tiên, mở terminal và chạy `cd .roo/tools/` để di chuyển đến thư mục tools của dự án, sau đó chạy `npm init -y` để khởi tạo package.json, và cuối cùng cài đặt các packages cần thiết bằng `npm install axios lodash` hoặc bất kỳ thư viện nào bạn cần. Thư mục `.roo/tools/` sẽ có package.json riêng, giúp quản lý dependencies độc lập cho mỗi dự án.

Việc sử dụng npm dependencies mở ra khả năng tích hợp với hầu hết các dịch vụ và API phổ biến. Bạn có thể sử dụng axios hoặc fetch để gọi REST API, sử dụng các SDK của AWS, Google Cloud hoặc Azure để tương tác với cloud services, hoặc sử dụng các thư viện xử lý dữ liệu như lodash, moment.js hoặc date-fns để thao tác với dữ liệu. Tuy nhiên, cần lưu ý rằng việc cài đặt quá nhiều dependencies có thể làm chậm quá trình khởi tạo công cụ và tăng kích thước dự án, vì vậy hãy cân nhắc kỹ và chỉ cài đặt những packages thực sự cần thiết.

## Ví Dụ Sử Dụng Chi Tiết

### Ví Dụ 1: Gọi API Với Axios

Một trong những use case phổ biến nhất của Custom Tools là tích hợp với các API bên ngoài. Dưới đây là ví dụ về cách tạo một công cụ để fetch dữ liệu từ API endpoint sử dụng thư viện axios. Công cụ này nhận vào một URL và trả về dữ liệu JSON từ endpoint đó, được định dạng đẹp mắt để AI có thể dễ dàng đọc và xử lý. Việc sử dụng axios thay vì fetch API mặc định cung cấp nhiều tiện ích hơn như automatic JSON transformation, request/response interceptors và better error handling.

```typescript
import { parametersSchema as z, defineCustomTool } from "@roo-code/types"
import axios from "axios"

export default defineCustomTool({
  name: "fetch_api",
  description: "Fetch data from an API endpoint",
  parameters: z.object({
    url: z.string().describe("API endpoint URL to fetch data from"),
  }),
  async execute({ url }) {
    try {
      const response = await axios.get(url)
      return JSON.stringify(response.data, null, 2)
    } catch (error) {
      return `Error fetching data: ${error.message}`
    }
  }
})
```

Công cụ này có thể được sử dụng trong nhiều tình huống khác nhau như lấy thông tin từ API của bên thứ ba, kiểm tra trạng thái của các microservices, hoặc fetch dữ liệu từ các endpoint nội bộ của dự án. AI sẽ tự động gọi công cụ này khi cần lấy dữ liệu từ internet, giúp đơn giản hóa quy trình tra cứu thông tin và tích hợp dữ liệu từ các nguồn bên ngoài.

### Ví Dụ 2: Gửi Thông Báo Đến Slack

Trong môi trường làm việc nhóm, việc gửi thông báo đến các kênh communication như Slack là rất quan trọng để giữ cho mọi người được cập nhật về tiến độ công việc. Ví dụ dưới đây minh họa cách tạo một công cụ để gửi thông báo đến Slack webhook, sử dụng biến môi trường để bảo mật thông tin đăng nhập. Việc sử dụng biến môi trường giúp bảo vệ các thông tin nhạy cảm như webhook URL và không vô tình expose chúng trong mã nguồn.

```typescript
import { parametersSchema as z, defineCustomTool } from "@roo-code/types"
import dotenv from "dotenv"
import path from "path"

dotenv.config({ path: path.join(__dirname, ".env") })

export default defineCustomTool({
  name: "notify_slack",
  description: "Send a notification to Slack channel",
  parameters: z.object({
    message: z.string().describe("Message to send to Slack"),
  }),
  async execute({ message }) {
    const webhookUrl = process.env.SLACK_WEBHOOK_URL
    if (!webhookUrl) return "Error: SLACK_WEBHOOK_URL not set in environment"
    
    try {
      const response = await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: message }),
      })
      
      if (response.ok) {
        return "Message sent successfully to Slack"
      } else {
        return `Failed to send message: ${response.status} ${response.statusText}`
      }
    } catch (error) {
      return `Error sending to Slack: ${error.message}`
    }
  }
})
```

Để sử dụng công cụ này, bạn cần tạo một file `.env` trong thư mục `.roo/tools/` với nội dung `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL`. Công cụ sẽ tự động đọc file .env và sử dụng các biến môi trường được định nghĩa. Bạn có thể mở rộng công cụ này để hỗ trợ nhiều tính năng hơn như gửi tin nhắn với định dạng rich text, thêm attachments hoặc gửi đến nhiều channels khác nhau.

### Ví Dụ 3: Công Cụ Tạo Code Theo Template

Mỗi dự án thường có các coding conventions và templates riêng, và việc tạo một custom tool để áp dụng những templates này sẽ đảm bảo tính nhất quán trong toàn bộ codebase. Ví dụ dưới đây tạo một công cụ để tạo React component với cấu trúc và imports chuẩn của dự án.

```typescript
import { parametersSchema as z, defineCustomTool } from "@roo-code/types"
import fs from "fs"
import path from "path"

export default defineCustomTool({
  name: "create_react_component",
  description: "Create a new React component with standard template",
  parameters: z.object({
    componentName: z.string().describe("Name of the component (PascalCase)"),
    withStyles: z.boolean().describe("Whether to include styled-components").optional(),
    withTypescript: z.boolean().describe("Whether to use TypeScript").default(true),
  }),
  async execute({ componentName, withStyles = false, withTypescript = true }) {
    const ext = withTypescript ? "tsx" : "jsx"
    const dir = path.join(process.cwd(), "src", "components")
    
    // Ensure directory exists
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
    
    const filePath = path.join(dir, `${componentName}.${ext}`)
    
    let content = `import React from 'react'\n`
    if (withStyles) {
      content += `import styled from 'styled-components'\n\n`
      content += `const Styled${componentName} = styled.div\`\n  /* Add your styles here */\n\`\n\n`
    }
    content += `export const ${componentName} = ({ children }) => {\n`
    content += `  return (\n`
    content += `    ${withStyles ? `<Styled${componentName}>` : `<div>`}\n`
    content += `      {children}\n`
    content += `    ${withStyles ? `</Styled${componentName}>` : `</div>`}\n`
    content += `  )\n`
    content += `}\n`
    content += `export default ${componentName}\n`
    
    fs.writeFileSync(filePath, content)
    return `Created ${componentName} component at ${filePath}`
  }
})
```

Công cụ này tự động tạo file component với cấu trúc chuẩn, bao gồm việc tạo thư mục nếu chưa tồn tại, thêm imports cần thiết và định dạng code theo chuẩn của dự án. Bạn có thể mở rộng template này để bao gồm các imports phổ biến khác như React hooks, context providers hoặc các thành phần UI chung của dự án.

### Ví Dụ 4: Công Cụ Kiểm Tra Coding Standards

Để đảm bảo chất lượng code, việc tích hợp các công cụ kiểm tra coding standards vào quy trình làm việc là rất quan trọng. Ví dụ dưới đây tạo một công cụ để kiểm tra xem một file có tuân thủ các quy tắc linting cơ bản hay không.

```typescript
import { parametersSchema as z, defineCustomTool } from "@roo-code/types"
import fs from "fs"

export default defineCustomTool({
  name: "check_coding_standards",
  description: "Check if a file follows project coding standards",
  parameters: z.object({
    filePath: z.string().describe("Path to the file to check"),
  }),
  async execute({ filePath }) {
    const results = []
    
    if (!fs.existsSync(filePath)) {
      return `Error: File not found at ${filePath}`
    }
    
    const content = fs.readFileSync(filePath, "utf-8")
    const lines = content.split("\n")
    
    // Check for console.log statements
    const consoleLogs = content.match(/console\.(log|warn|error|debug)\(/g)
    if (consoleLogs) {
      results.push(`⚠️ Found ${consoleLogs.length} console statement(s) - consider removing for production`)
    }
    
    // Check for TODO comments
    const todos = content.match(/\/\/\s*TODO[^\n]*/gi)
    if (todos) {
      results.push(`📝 Found ${todos.length} TODO comment(s) - review for completion`)
    }
    
    // Check line length
    const longLines = lines.filter((line, idx) => line.length > 120)
    if (longLines.length > 0) {
      results.push(`📏 Found ${longLines.length} line(s) exceeding 120 characters`)
    }
    
    // Check for trailing whitespace
    const trailingWhitespace = lines.filter(line => line.trimEnd() !== line)
    if (trailingWhitespace.length > 0) {
      results.push(`🔍 Found ${trailingWhitespace.length} line(s) with trailing whitespace`)
    }
    
    if (results.length === 0) {
      return "✅ File passes all coding standard checks"
    }
    
    return `Coding Standards Report for ${filePath}:\n${results.join("\n")}`
  }
})
```

Công cụ kiểm tra này có thể được mở rộng để bao gồm nhiều quy tắc hơn như kiểm tra imports ordering, kiểm tra naming conventions, hoặc tích hợp với các công cụ ESLint và Prettier. Việc tự động hóa quy trình review code giúp đảm bảo tính nhất quán và giảm thời gian review thủ công.

## Giới Hạn và Lưu Ý Quan Trọng

### Các Giới Hạn Kỹ Thuật

Custom Tools có một số giới hạn kỹ thuật quan trọng mà người dùng cần lưu ý trong quá trình sử dụng. Đầu tiên, tất cả các công cụ tùy chỉnh được tự động phê duyệt khi tính năng được bật — điều này có nghĩa là Roo sẽ không hỏi xin phép trước khi thực thi chúng, vừa là ưu điểm về tốc độ vừa là rủi ro về bảo mật nếu công cụ không được viết cẩn thận. Thứ hai, kết quả trả về phải là string — công cụ không thể trả về các kiểu dữ liệu phức tạp như objects hoặc arrays một cách trực tiếp, mà phải serialize chúng thành string (thường bằng JSON.stringify). Thứ ba, không hỗ trợ interactive input — công cụ không thể yêu cầu người dùng nhập liệu trong quá trình thực thi, tất cả các tham số cần thiết phải được truyền vào ngay từ đầu.

Ngoài ra, còn có vấn đề về cache invalidation — sau khi thêm hoặc sửa đổi công cụ, bạn có thể cần reload cửa sổ VS Code để Roo nhận ra các thay đổi. Điều này có thể gây gián đoạn nhỏ trong quy trình làm việc, đặc biệt khi bạn đang trong quá trình phát triển và testing các công cụ mới. Một giới hạn khác là không có cơ chế sandboxing mạnh — các công cụ chạy với quyền của tiến trình VS Code, vì vậy một công cụ độc hại có thể gây ra hậu quả nghiêm trọng.

### So Sánh với MCP

Khi quyết định giữa Custom Tools và MCP, điều quan trọng là hiểu rõ sự khác biệt và use case phù hợp cho mỗi giải pháp. MCP (Model Context Protocol) được thiết kế để tích hợp với các dịch vụ bên ngoài như tìm kiếm web, API của bên thứ ba và các công cụ SaaS — đây là giải pháp phù hợp khi bạn cần kết nối với các hệ thống có sẵn và không muốn tự viết logic integration. Custom Tools thì nhẹ hơn và phù hợp hơn cho logic nội bộ của dự án — những thao tác đặc thù mà chỉ dự án của bạn mới cần, không yêu cầu kết nối với các dịch vụ bên ngoài.

Về độ phức tạp, MCP thường yêu cầu cấu hình nhiều hơn và có thể khó debug hơn do nature của việc kết nối với các dịch vụ bên ngoài. Custom Tools cho phép bạn viết logic bằng TypeScript/JavaScript quen thuộc, dễ dàng test và debug hơn. Về hiệu suất, Custom Tools thường có latency thấp hơn vì chúng chạy local và không cần giao tiếp qua network với các dịch vụ bên ngoài. Tuy nhiên, nếu bạn cần tích hợp với nhiều dịch vụ bên ngoài khác nhau, MCP có thể là lựa chọn tốt hơn do cung cấp một framework chuẩn hóa cho việc quản lý các connections.

## Best Practices và Khuyến Nghị

### Bảo Mật và An Toàn

Khi làm việc với Custom Tools, bảo mật nên là ưu tiên hàng đầu vì các công cụ này chạy với quyền hạn cao và được tự động phê duyệt. Không bao giờ lưu trữ thông tin nhạy cảm như API keys, passwords hoặc tokens trực tiếp trong mã nguồn — luôn sử dụng biến môi trường và file .env để bảo vệ thông tin này. Review kỹ tất cả các công cụ trước khi thêm vào dự án, đặc biệt là các công cụ được download từ internet hoặc chia sẻ bởi người khác. Tránh tạo các công cụ có thể thực thi lệnh hệ thống hoặc thao tác với file quan trọng trừ khi thực sự cần thiết và đã được review cẩn thận.

### Tổ Chức và Maintainability

Để duy trì tính maintainability trong dài hạn, hãy tổ chức các custom tools một cách có cấu trúc. Đặt tên công cụ rõ ràng và mô tả chi tiết để AI có thể hiểu và sử dụng chúng đúng cách. Tách riêng các công cụ có chức năng khác nhau thành các files riêng để dễ dàng quản lý và update. Viết comments và documentation cho các công cụ phức tạp để người khác (hoặc chính bạn trong tương lai) có thể hiểu và modify nếu cần. Cuối cùng, hãy version control các công cụ bằng cách thêm chúng vào git repository để theo dõi thay đổi và có thể rollback khi cần thiết.

---

Roo Custom Tools là một tính năng mạnh mẽ cho phép bạn mở rộng khả năng của Roo Code và tự động hóa các quy trình đặc thù của dự án. Bằng cách tuân thủ các best practices và hiểu rõ các giới hạn, bạn có thể tận dụng tối đa tiềm năng của công cụ này để nâng cao năng suất và đảm bảo tính nhất quán trong quy trình phát triển phần mềm.