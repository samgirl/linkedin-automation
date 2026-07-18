/**
 * PROS Chrome Extension - Content Script
 * Captures page content and communicates with background script.
 */

class ContentCapture {
  constructor() {
    this.init();
  }

  init() {
    // Listen for messages from background/popup
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      switch (message.type) {
        case 'CAPTURE_PAGE':
          this.capturePage().then(sendResponse);
          return true;
        case 'CAPTURE_SELECTION':
          this.captureSelection().then(sendResponse);
          return true;
        case 'GET_PAGE_INFO':
          sendResponse(this.getPageInfo());
          return true;
      }
    });
  }

  async capturePage() {
    const metadata = this.extractMetadata();
    const content = this.extractContent();
    
    return {
      url: window.location.href,
      title: document.title,
      content: content,
      website: this.detectWebsite(),
      author: metadata.author,
      description: metadata.description,
      publishDate: metadata.publishDate,
      keywords: metadata.keywords,
      images: metadata.images.slice(0, 5)
    };
  }

  async captureSelection() {
    const selection = window.getSelection();
    const selectedText = selection ? selection.toString().trim() : '';
    
    return {
      url: window.location.href,
      title: document.title,
      selectedText: selectedText,
      website: this.detectWebsite(),
      context: this.getSelectionContext(selection)
    };
  }

  getPageInfo() {
    return {
      url: window.location.href,
      title: document.title,
      website: this.detectWebsite()
    };
  }

  extractMetadata() {
    // Author
    const authorMeta = document.querySelector('meta[name="author"]');
    const authorOG = document.querySelector('meta[property="og:author"]');
    const author = authorMeta?.content || authorOG?.content || this.extractAuthorFromPage();
    
    // Description
    const descMeta = document.querySelector('meta[name="description"]');
    const descOG = document.querySelector('meta[property="og:description"]');
    const description = descMeta?.content || descOG?.content || '';
    
    // Publish date
    const dateMeta = document.querySelector('meta[property="article:published_time"]');
    const timeEl = document.querySelector('time[datetime]');
    const publishDate = dateMeta?.content || timeEl?.getAttribute('datetime') || null;
    
    // Keywords
    const keywordsMeta = document.querySelector('meta[name="keywords"]');
    const keywords = keywordsMeta?.content?.split(',').map(k => k.trim()) || [];
    
    // Images
    const ogImages = document.querySelectorAll('meta[property="og:image"]');
    const images = Array.from(ogImages).map(meta => meta.content).filter(Boolean);
    
    return { author, description, publishDate, keywords, images };
  }

  extractContent() {
    // Remove non-content elements
    const clone = document.body.cloneNode(true);
    const removeSelectors = [
      'script', 'style', 'nav', 'footer', 'header', 'aside',
      '.ad', '.advertisement', '.sidebar', '.comments', '.related'
    ];
    
    removeSelectors.forEach(selector => {
      clone.querySelectorAll(selector).forEach(el => el.remove());
    });
    
    // Get main content
    const article = clone.querySelector('article') || 
                    clone.querySelector('[role="main"]') ||
                    clone.querySelector('main') ||
                    clone.body;
    
    // Extract text, preserving some structure
    return this.extractTextWithStructure(article);
  }

  extractTextWithStructure(element) {
    const texts = [];
    
    const walk = (node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent.trim();
        if (text) texts.push(text);
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        const tag = node.tagName.toLowerCase();
        
        // Add line breaks for block elements
        if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br'].includes(tag)) {
          texts.push('\n');
        }
        
        // Add header markers
        if (tag.startsWith('h')) {
          texts.push(`[${tag.toUpperCase()}] `);
        }
        
        // Add list markers
        if (tag === 'li') {
          texts.push('• ');
        }
        
        node.childNodes.forEach(walk);
      }
    };
    
    walk(element);
    
    // Clean up multiple newlines and spaces
    return texts.join('')
      .replace(/\n{3,}/g, '\n\n')
      .replace(/\s+/g, ' ')
      .trim();
  }

  extractAuthorFromPage() {
    // Try common author selectors
    const selectors = [
      '[class*="author"]',
      '[class*="byline"]',
      '[rel="author"]',
      '.post-author',
      '.article-author'
    ];
    
    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el?.textContent) {
        return el.textContent.trim().split('\n')[0].trim();
      }
    }
    
    return null;
  }

  detectWebsite() {
    const url = window.location.href;
    
    if (url.includes('linkedin.com')) return 'linkedin';
    if (url.includes('github.com')) return 'github';
    if (url.includes('arxiv.org')) return 'arxiv';
    if (url.includes('medium.com')) return 'medium';
    if (url.includes('twitter.com') || url.includes('x.com')) return 'twitter';
    if (url.includes('reddit.com')) return 'reddit';
    if (url.includes('youtube.com')) return 'youtube';
    if (url.includes('stackoverflow.com')) return 'stackoverflow';
    
    return 'web';
  }

  getSelectionContext(selection) {
    if (!selection || selection.rangeCount === 0) return null;
    
    const range = selection.getRangeAt(0);
    const container = range.commonAncestorContainer;
    
    // Get parent element context
    const parent = container.nodeType === Node.TEXT_NODE 
      ? container.parentElement 
      : container;
    
    return {
      parentTag: parent?.tagName?.toLowerCase(),
      parentText: parent?.textContent?.substring(0, 200)
    };
  }
}

// Initialize content capture
new ContentCapture();
