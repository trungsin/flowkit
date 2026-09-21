# Research Report: Landing page tiếng Việt trên trang home

**Date:** 2026-09-20 20:31
**Scope:** `flowkit.datxanhmientrung.ai` `/` hiện là ops dashboard. Cần landing public tiếng Việt, không phá console.
**Sources:** 8 (SaaS LP 2026, CTA tiếng Việt, copy formulas, UI-UX Pro Max, codebase dashboard)

## Executive Summary

`/` đang render `DashboardPage` trong shell sidebar (KPI, pipeline, logs). Đó là **ops console**, không phải landing. Domain public + không auth → khách vào thấy bảng điều khiển trống, `extension_connected: false`.

Khuyến nghị **KISS:** `/` = landing full-bleed tiếng Việt, **không sidebar**. Dashboard dời sang `/dashboard`. CTA chính: **Vào bảng điều khiển**. Copy mặc định `vi` trên domain production. Giữ token dark hiện tại (Geist), không đổi sang Inter/light của design-system generic.

Minimum viable: Hero + 3 bước + proof (thumbnail sẵn) + FAQ + CTA cuối. Không form, không pricing, không video background nặng.

## Current state

| Item | Now |
|---|---|
| Route `/` | `DashboardPage` trong `Layout` (sidebar + header) |
| i18n | 7 ngôn ngữ; `vi` đủ cho chrome UI; default = `navigator.language` |
| Guide `/guide` | Hướng dẫn cài extension — operator, không phải marketing |
| Proof assets | `docs/images/thumbnail_*.jpg`, scene stills — dùng được trên LP |
| Auth | Không có |

Vấn đề: landing cần 1 mục tiêu / 1 CTA. Dashboard cần nhiều nav. Hai việc không chung 1 layout.

## Architecture (recommended)

```
/                  LandingPage     no sidebar, full viewport
/dashboard         DashboardPage   current home, inside Layout
/projects …        unchanged
```

```
Browser ── GET / ──► Landing (public, vi)
              CTA "Vào bảng điều khiển" ──► /dashboard (ops shell)
              CTA phụ "Xem hướng dẫn"   ──► /guide
```

**Không** làm `/app/*` nested rewrite — quá lớn, YAGNI.

`App.tsx`: tách route `/` ra ngoài `Layout`. Nav item đầu: `/dashboard`.

SPA FastAPI catch-all đã serve `index.html` cho `/` và `/dashboard` — không đổi backend.

SEO: SPA JS-only. Domain nội bộ/ops thì chấp nhận. Muốn index Google sau này mới SSR.

## Copy tiếng Việt

Công thức 2026: **outcome + audience − pain**, không “nền tảng all-in-one”. CTA tiếng Việt: động từ mạnh + lợi ích; tránh “Gửi/Submit”. Ngôi thứ nhất khi phù hợp (“video của tôi”). Microcopy dưới nút để giảm ma sát.

Giữ tên **FLOW KIT**. Thuật ngữ kỹ thuật: giải thích 1 lần, không dịch gượng (`pipeline`, `scene`, `extension`).

### Hero (draft)

| Slot | Copy |
|---|---|
| Pre | Hệ thống làm video AI qua Google Flow |
| H1 | Nhân vật không đổi mặt. Video ra YouTube. |
| Sub | Flow Kit chạy cả pipeline: ảnh tham chiếu → cảnh → clip 8 giây → thuyết minh → ghép phim. Một dashboard, không copy-paste prompt từng shot. |
| CTA chính | Vào bảng điều khiển |
| CTA phụ | Xem hướng dẫn cài đặt |
| Micro | Cần Chrome đã login flow.google.com. Chưa có tài khoản công khai. |

H1 yếu cần tránh: “Nền tảng AI video thế hệ mới”.

### 3 bước (How it works)

1. **Ghim nhân vật** — 1 ảnh tham chiếu / entity. Cảnh sau chỉ tả hành động.
2. **Chạy pipeline** — batch ảnh → video → review. Server tự throttle.
3. **Ghép & đăng** — TTS + overlay + concat. Thumbnail + SEO YouTube.

### Benefit (không feature)

| Feature | Benefit (vi) |
|---|---|
| Reference images | Cùng 1 mặt bác sĩ / phi công xuyên 4–50 cảnh |
| Scene prompts = action only | Không phải tả lại quần áo mỗi shot |
| Batch API | Không ngồi bấm từng clip |
| Dashboard i18n | Làm việc bằng tiếng Việt |

### FAQ (gỡ objection)

- Cần Google Flow? Có. Extension + tab `flow.google.com` phải mở.
- Chạy headless được không? Không. Flow ký request trong page.
- Upscale 4K? Chưa port trên Veo. Giữ 1080p.
- Ai được vào dashboard? Hiện **mọi người có URL** — chưa auth. Ghi rõ.

### CTA tiếng Việt — dùng / tránh

| Tránh | Dùng |
|---|---|
| Bắt đầu | Vào bảng điều khiển |
| Tìm hiểu thêm | Xem video mẫu / Xem hướng dẫn |
| Đăng ký ngay | (không có signup) |
| Learn more | Xem pipeline hoạt động |

Lặp CTA: hero + sau proof + cuối trang. 1 primary / section.

## Design

UI-UX script gợi Video-First Hero + Bento + Inter/light + CTA cam. **Lệch** dashboard hiện tại (dark, Geist, accent token).

Quyết định: **bám token CSS dashboard**. Dark cinematic. CTA = `--accent` contrast. Bento 4 ô pipeline (Refs / Images / Videos / Concat). Proof = grid thumbnail sẵn trong `docs/images/`.

Không: emoji icon, video background (CLS + 3.5G disk VPS), form lead, pop-up.

A11y: contrast 4.5:1, focus ring, `prefers-reduced-motion`, CTA ≥44px, H1 duy nhất.

Mobile: hero stack, CTA full-width, proof 2 cột.

## Page flow (MVP)

```
1. Nav tối giản: logo + ngôn ngữ + "Vào bảng điều khiển"
2. Hero
3. Proof stills (6 thumbnail README)
4. 3 bước
5. Bento 4 giai đoạn
6. FAQ
7. Final CTA
```

Bỏ: pricing, logo cloud giả, testimonial bịa, scarcity giả.

## Implementation (when building)

1. `LandingPage.tsx` — không fetch `/api/projects` (tránh spinner ops trên home).
2. Keys `landing.*` trong `translations.ts` — **vi viết trước**, en mirror. Không để hardcode.
3. `App.tsx`: `/` ngoài Layout; nav dashboard → `/dashboard`.
4. Default lang: nếu host chứa `datxanhmientrung.ai` → `vi`, else detect.
5. `index.html` title/description tiếng Việt cho tab.
6. CTA `Link to="/dashboard"` và `/guide`.
7. Copy thumbnail vào `dashboard/public/landing/` (không phụ thuộc `docs/` trên prod).
8. Test: `/` không sidebar; `/dashboard` giữ KPI; mobile 375.

Ước lượng: 1 page + i18n + route split. Không Docker, không backend mới.

## Security

Landing **không** thay thế auth. URL dashboard vẫn public. Ghi trên LP. Cloudflare Access = bước riêng sau DNS.

## Comparative

| Option | Pros | Cons | Pick |
|---|---|---|---|
| A. `/` landing, `/dashboard` ops | Đúng public domain, đổi ít | Bookmark `/` cũ gãy | **Yes** |
| B. Landing đè lên DashboardPage | Nhanh | Ops mất home, 2 mục tiêu 1 trang | No |
| C. Nested `/app/*` | Sạch lâu dài | Đụng mọi NavLink | Later |
| D. Subdomain `app.` | Tách hẳn | DNS + 2 tunnel | Overkill |

## Resources

- [SaaS LP 2026 checklist](https://www.moydus.com/blog/saas-landing-page-best-practices-2026) — headline = pain/outcome
- [Orbix 2026 examples](https://www.orbix.studio/blogs/saas-landing-page-examples) — 1 outcome, 1 CTA, product visual above fold
- [CTA tiếng Việt](https://phuctdigital.com/tam-quan-trong-cua-cta-tren-landing-page-va-cach-viet-cta-hieu-qua/) — động từ mạnh, ngôi 1, 3 vị trí CTA
- Copy skill: AIDA/PAS, hero = promise + how + CTA + proof
- Code: `dashboard/src/App.tsx`, `pages/DashboardPage.tsx`, `i18n/translations.ts`

## Next steps

1. User chốt: CTA chính = vào dashboard (ops) hay chỉ marketing/gallery.
2. Implement option A.
3. Deploy `scripts/deploy-vps.sh` sau khi DNS domain xong.

## Unresolved questions

1. Khách vào domain là **operator** (muốn dashboard) hay **khách xem sản phẩm**? Nếu 100% operator, landing có thể thừa — chỉ cần `/` dashboard + default `vi`.
2. Có khóa `/dashboard` bằng Cloudflare Access không?
3. Default language: luôn `vi` trên domain này, hay giữ detect browser?
4. Dùng thumbnail thật từ `docs/images` hay generate hero mới?
