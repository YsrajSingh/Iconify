/**
 * Logo Fetcher - Cloudflare Worker
 *
 * A lightweight edge implementation for fetching company logos.
 */

const CACHE_TTL = 3600; // 1 hour

/**
 * Fetch logo from logo.dev search API with Google favicon fallback
 */
async function fetchFromLogoDev(domain, apiKey) {
  // Try logo.dev search API
  const searchUrl = `https://www.logo.dev/api/search?q=${encodeURIComponent(domain)}`;
  const headers = apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {};

  try {
    const response = await fetch(searchUrl, { headers });
    if (response.ok) {
      const data = await response.json();
      if (data && data.length > 0) {
        // Try exact match first
        const exactMatch = data.find(item => item.domain?.toLowerCase() === domain.toLowerCase());
        if (exactMatch?.logo_url) return exactMatch.logo_url;
        // Return first result
        if (data[0]?.logo_url) return data[0].logo_url;
      }
    }
  } catch (error) {
    console.error('LogoDev error:', error);
  }

  // Fall back to Google favicon service
  const googleUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
  try {
    const response = await fetch(googleUrl, { method: 'HEAD', redirect: 'follow' });
    if (response.ok) return googleUrl;
  } catch (error) {
    console.error('Google favicon error:', error);
  }

  return null;
}

/**
 * Fetch logo from Brandfetch search API with DuckDuckGo fallback
 */
async function fetchFromBrandfetch(domain, apiKey) {
  // Try Brandfetch search API
  const searchUrl = `https://api.brandfetch.io/v2/search/${encodeURIComponent(domain)}`;
  const headers = apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {};

  try {
    const response = await fetch(searchUrl, { headers });
    if (response.ok) {
      const data = await response.json();
      if (data && data.length > 0) {
        // Try exact match first
        const exactMatch = data.find(item => item.domain?.toLowerCase() === domain.toLowerCase());
        if (exactMatch?.icon) return exactMatch.icon;
        // Return first result
        if (data[0]?.icon) return data[0].icon;
      }
    }
  } catch (error) {
    console.error('Brandfetch error:', error);
  }

  // Fall back to DuckDuckGo icon service
  const ddgUrl = `https://icons.duckduckgo.com/ip3/${domain}.ico`;
  try {
    const response = await fetch(ddgUrl, { method: 'HEAD' });
    if (response.ok) {
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('image') || contentType.includes('icon')) {
        return ddgUrl;
      }
    }
  } catch (error) {
    console.error('DuckDuckGo error:', error);
  }

  return null;
}

/**
 * Scrape logo from website
 */
async function scrapeFromWebsite(domain) {
  const url = `https://${domain}`;

  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });

    if (!response.ok) return null;

    const html = await response.text();

    // Try apple-touch-icon first (usually high quality)
    const touchIconMatch = html.match(/<link[^>]+rel=["']apple-touch-icon[^"']*["'][^>]+href=["']([^"']+)["']/i)
      || html.match(/<link[^>]+href=["']([^"']+)["'][^>]+rel=["']apple-touch-icon[^"']*["']/i);
    if (touchIconMatch?.[1]) {
      const logoUrl = resolveUrl(touchIconMatch[1], url);
      if (await verifyImage(logoUrl)) return logoUrl;
    }

    // Try og:image
    const ogImageMatch = html.match(/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/i)
      || html.match(/<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']/i);
    if (ogImageMatch?.[1]) {
      const logoUrl = resolveUrl(ogImageMatch[1], url);
      if (await verifyImage(logoUrl)) return logoUrl;
    }

    // Try favicon
    const faviconMatch = html.match(/<link[^>]+rel=["'](?:shortcut )?icon["'][^>]+href=["']([^"']+)["']/i)
      || html.match(/<link[^>]+href=["']([^"']+)["'][^>]+rel=["'](?:shortcut )?icon["']/i);
    if (faviconMatch?.[1]) {
      const logoUrl = resolveUrl(faviconMatch[1], url);
      if (await verifyImage(logoUrl)) return logoUrl;
    }

    // Default favicon
    const defaultFavicon = `${url}/favicon.ico`;
    if (await verifyImage(defaultFavicon)) return defaultFavicon;

  } catch (error) {
    console.error('Scraper error:', error);
  }
  return null;
}

/**
 * Resolve relative URL to absolute
 */
function resolveUrl(href, base) {
  if (href.startsWith('http://') || href.startsWith('https://')) {
    return href;
  }
  if (href.startsWith('//')) {
    return 'https:' + href;
  }
  const baseUrl = new URL(base);
  if (href.startsWith('/')) {
    return `${baseUrl.origin}${href}`;
  }
  return `${baseUrl.origin}/${href}`;
}

/**
 * Verify URL points to a valid image
 */
async function verifyImage(url) {
  try {
    const response = await fetch(url, { method: 'HEAD' });
    if (response.ok) {
      const contentType = response.headers.get('content-type') || '';
      return contentType.includes('image') || contentType.includes('icon') ||
        url.toLowerCase().match(/\.(png|jpg|jpeg|svg|webp|ico|gif)$/);
    }
  } catch {
    // Ignore verification errors
  }
  return false;
}

/**
 * Normalize domain
 */
function normalizeDomain(domain) {
  domain = domain.toLowerCase().trim();
  for (const prefix of ['https://', 'http://', 'www.']) {
    if (domain.startsWith(prefix)) {
      domain = domain.slice(prefix.length);
    }
  }
  return domain.replace(/\/$/, '');
}

/**
 * Main handler
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check
    if (path === '/health') {
      return Response.json({
        status: 'healthy',
        version: '1.0.0',
        runtime: 'cloudflare-worker'
      }, { headers: corsHeaders });
    }

    // Logo endpoint: /logo/{domain}
    const logoMatch = path.match(/^\/logo\/(.+)$/);
    if (logoMatch) {
      const domain = normalizeDomain(logoMatch[1]);
      const source = url.searchParams.get('source');
      const all = url.searchParams.get('all') === 'true';

      // Check cache
      const cacheKey = new Request(`${url.origin}/cache/${domain}`, request);
      const cache = caches.default;

      if (!all && !source) {
        const cachedResponse = await cache.match(cacheKey);
        if (cachedResponse) {
          return cachedResponse;
        }
      }

      const logodevKey = env.LOGODEV_API_KEY;
      const brandfetchKey = env.BRANDFETCH_API_KEY;

      if (all) {
        // Fetch from all sources
        const results = [];
        const errors = {};

        const [logodevUrl, brandfetchUrl, scraperUrl] = await Promise.allSettled([
          fetchFromLogoDev(domain, logodevKey),
          fetchFromBrandfetch(domain, brandfetchKey),
          scrapeFromWebsite(domain)
        ]);

        if (logodevUrl.status === 'fulfilled' && logodevUrl.value) {
          results.push({ domain, url: logodevUrl.value, source: 'logodev' });
        } else if (logodevUrl.status === 'rejected') {
          errors.logodev = logodevUrl.reason?.message || 'Failed';
        }

        if (brandfetchUrl.status === 'fulfilled' && brandfetchUrl.value) {
          results.push({ domain, url: brandfetchUrl.value, source: 'brandfetch' });
        } else if (brandfetchUrl.status === 'rejected') {
          errors.brandfetch = brandfetchUrl.reason?.message || 'Failed';
        }

        if (scraperUrl.status === 'fulfilled' && scraperUrl.value) {
          results.push({ domain, url: scraperUrl.value, source: 'scraper' });
        } else if (scraperUrl.status === 'rejected') {
          errors.scraper = scraperUrl.reason?.message || 'Failed';
        }

        return Response.json({ domain, results, errors }, { headers: corsHeaders });
      }

      // Single source or fallback chain
      let logoUrl = null;
      let usedSource = null;

      const sources = source
        ? [source]
        : ['logodev', 'brandfetch', 'scraper'];

      for (const src of sources) {
        switch (src) {
          case 'logodev':
            logoUrl = await fetchFromLogoDev(domain, logodevKey);
            if (logoUrl) usedSource = 'logodev';
            break;
          case 'brandfetch':
            logoUrl = await fetchFromBrandfetch(domain, brandfetchKey);
            if (logoUrl) usedSource = 'brandfetch';
            break;
          case 'scraper':
            logoUrl = await scrapeFromWebsite(domain);
            if (logoUrl) usedSource = 'scraper';
            break;
        }
        if (logoUrl) break;
      }

      if (logoUrl) {
        const response = Response.json({
          domain,
          url: logoUrl,
          source: usedSource
        }, { headers: corsHeaders });

        // Cache successful responses
        const cacheResponse = new Response(response.body, response);
        cacheResponse.headers.set('Cache-Control', `public, max-age=${CACHE_TTL}`);
        ctx.waitUntil(cache.put(cacheKey, cacheResponse.clone()));

        return response;
      }

      return Response.json(
        { error: `No logo found for domain: ${domain}` },
        { status: 404, headers: corsHeaders }
      );
    }

    // Not found
    return Response.json(
      { error: 'Not found. Use /logo/{domain} or /health' },
      { status: 404, headers: corsHeaders }
    );
  }
};
