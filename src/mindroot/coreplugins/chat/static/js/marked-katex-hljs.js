import { marked } from './marked.esm.js'
import hljs from './highlight.js'
//import katex from 'katex'

marked.setOptions({
  langPrefix: 'hljs lang-',
  pedantic: false,
  gfm: true,
  breaks: false,
  tables: true,
  sanitize: false,
  smartLists: true, 
  smartypants: false,
  xhtml: false, 
  highlight: function (code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  },
})

const renderer = {
  heading(text, level) {
    const escapedText = text.toLowerCase().replace(/[^\w]+/g, '-')
    return `<h${level}>
        <a name="${escapedText}" class="anchor" href="#${escapedText}">
          <span class="header-link"></span>
        </a>
        ${text}
      </h${level}>`
  },
  blockTex(src) {
    console.log(src)
  },
}

const extensions = [
  {
    name: 'inline-tex',
    level: 'inline',
    start(src) {
      return src.match(/\$[^$\n]/)?.index
    },
    tokenizer(src) {
      const rule = /(\$[^$\n]+?\$)/g
      const match = rule.exec(src)
      if (match) {
        const token = {
          type: 'inline-tex',
          raw: match.input,
          tokens: [],
        }
        const tex = match[1].slice(1, -1).trim()
        this.lexer.inline(
          match.input.replaceAll(
            match[1],
            katex.renderToString(tex, {
              strict: false,
              displayMode: false,
            })
          ),
          token.tokens
        )
        return token
      }
      return false
    },
    renderer(token) {
      return this.parser.parseInline(token.tokens)
    },
  },
  {
    name: 'block-tex',
    level: 'block',
    start(src) {
      return src.match(/\s*\$\$[^$]/)?.index
    },
    tokenizer(src) {
      const rule = /^(\s*\$\$[^$]+?\$\$\s*)$/m
      const match = rule.exec(src)
      console.log(match)
      if (match) {
        const token = {
          type: 'blockTex', // block-tex
          // raw: match.input,
          tokens: [],
        }
        const tex = match[1].trim().slice(2, -2).trim()
        console.log(match.input)
        token.raw = match.input.replaceAll(
          match[1],
          katex.renderToString(tex, {
            strict: false,
            displayMode: true,
          })
        )

        this.lexer.blockTokens(token.raw, token.tokens)
        return token
      }
      // return false
    },
    renderer(token) {
      console.log(token)
      // return token.raw
      return this.parser.parse(token.tokens)
    },
  },
]

// function walkTokens(token) {
//   // Post-processing on the completed token tree
// }
// marked.use({ renderer, extensions, walkTokens })

marked.use({ renderer, extensions })

export default (text) => marked(text)
