<template>
  <main class="lp-main">

    <!-- ═══════ HERO ═══════ -->
    <section class="lp-shell lp-hero">
      <div class="lp-hero-left">
        <div class="lp-eyebrow"><span class="lp-eyebrow-dot"></span>{{ t("landing.eyebrow") }}</div>
        <h1 class="lp-h1">{{ t("landing.h1") }}</h1>
        <p class="lp-subtitle">{{ t("landing.subtitle") }}</p>
        <div class="lp-actions">
          <a
            v-if="registrationEnabled"
            class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill"
            href="/accounts/signup/"
          >{{ t("landing.tryFree") }}</a>
          <a
            v-else
            class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill eb-btn-disabled"
          >{{ t("landing.tryFree") }}</a>
          <a class="lp-btn lp-btn-ghost lp-btn-lg" href="#how">{{ t("landing.howItWorks") }}</a>
        </div>
        <div class="lp-pills">
          <span class="lp-pill">{{ t("landing.pillMonthlyPlanning") }}</span>
          <span class="lp-pill">{{ t("landing.pillPlanVsReality") }}</span>
          <span class="lp-pill">{{ t("landing.pillCoachAthlete") }}</span>
        </div>
      </div>
      <div class="lp-hero-right" style="position:relative;">
        <div class="lp-panel">
          <div class="lp-panel-chrome">
            <span class="lp-dot" style="background:#f43f5e;"></span>
            <span class="lp-dot" style="background:#f59e0b;"></span>
            <span class="lp-dot" style="background:#c8ff00;"></span>
            <span class="lp-panel-label">{{ t("landing.mockupTitle") }}</span>
          </div>
          <div class="lp-panel-body">
            <div class="lp-week-label">{{ t("landing.mockupWeekLabel") }}</div>
            <div class="lp-week-grid">
              <div class="lp-day done">
                <div class="lp-day-name">{{ t("landing.mockupMon") }}</div>
                <span class="lp-day-icon">🏃</span>
                <div class="lp-day-val">12 km</div>
              </div>
              <div class="lp-day done">
                <div class="lp-day-name">{{ t("landing.mockupTue") }}</div>
                <span class="lp-day-icon">🏃</span>
                <div class="lp-day-val">16 km</div>
              </div>
              <div class="lp-day rest">
                <div class="lp-day-name">{{ t("landing.mockupWed") }}</div>
                <span class="lp-day-icon">—</span>
                <div class="lp-day-val">{{ t("landing.mockupRest") }}</div>
              </div>
              <div class="lp-day done">
                <div class="lp-day-name">{{ t("landing.mockupThu") }}</div>
                <span class="lp-day-icon">🚴</span>
                <div class="lp-day-val">45 km</div>
              </div>
              <div class="lp-day plan">
                <div class="lp-day-name">{{ t("landing.mockupFri") }}</div>
                <span class="lp-day-icon">🏃</span>
                <div class="lp-day-val">10 km</div>
              </div>
              <div class="lp-day rest">
                <div class="lp-day-name">{{ t("landing.mockupSat") }}</div>
                <span class="lp-day-icon">—</span>
                <div class="lp-day-val">{{ t("landing.mockupRest") }}</div>
              </div>
              <div class="lp-day plan">
                <div class="lp-day-name">{{ t("landing.mockupSun") }}</div>
                <span class="lp-day-icon">🏃</span>
                <div class="lp-day-val">28 km</div>
              </div>
            </div>
            <div class="lp-activity">
              <div class="lp-activity-icon run">🏃</div>
              <div class="lp-activity-info">
                <div class="lp-activity-name">{{ t("landing.mockupActivity1") }}</div>
                <div class="lp-activity-meta">16.2 km · 4:52 /km · 1h 18m</div>
              </div>
              <span class="lp-badge done">{{ t("landing.mockupDone") }}</span>
            </div>
            <div class="lp-activity">
              <div class="lp-activity-icon bike">🚴</div>
              <div class="lp-activity-info">
                <div class="lp-activity-name">{{ t("landing.mockupActivity2") }}</div>
                <div class="lp-activity-meta">44.8 km · 26.4 km/h · 1h 42m</div>
              </div>
              <span class="lp-badge done">{{ t("landing.mockupDone") }}</span>
            </div>
          </div>
        </div>
        <div class="lp-float">
          <div class="lp-float-label">{{ t("landing.mockupWeeklyVolume") }}</div>
          <div class="lp-float-val">54 km</div>
          <div class="lp-float-sub">{{ t("landing.mockupCompleted") }}</div>
        </div>
      </div>
    </section>

    <!-- ═══════ FEATURES ═══════ -->
    <section id="features" class="lp-section fade-up">
      <div class="lp-shell">
        <div class="lp-label">{{ t("landing.featuresLabel") }}</div>
        <h2 class="lp-section-title">{{ t("landing.featuresTitle") }}</h2>
        <p class="lp-section-lead">{{ t("landing.featuresLead") }}</p>
        <div class="lp-grid-3">
          <article class="lp-card">
            <div class="lp-card-icon">📅</div>
            <div class="lp-card-title">{{ t("landing.feature1Title") }}</div>
            <p class="lp-card-copy">{{ t("landing.feature1Copy") }}</p>
          </article>
          <article class="lp-card">
            <div class="lp-card-icon">✓</div>
            <div class="lp-card-title">{{ t("landing.feature2Title") }}</div>
            <p class="lp-card-copy">{{ t("landing.feature2Copy") }}</p>
          </article>
          <article class="lp-card">
            <div class="lp-card-icon">⚡</div>
            <div class="lp-card-title">{{ t("landing.feature3Title") }}</div>
            <p class="lp-card-copy">{{ t("landing.feature3Copy") }}</p>
          </article>
          <article class="lp-card">
            <div class="lp-card-icon">📁</div>
            <div class="lp-card-title">{{ t("landing.feature4Title") }}</div>
            <p class="lp-card-copy">{{ t("landing.feature4Copy") }}</p>
          </article>
          <article class="lp-card">
            <div class="lp-card-icon">👥</div>
            <div class="lp-card-title">{{ t("landing.feature5Title") }}</div>
            <p class="lp-card-copy">{{ t("landing.feature5Copy") }}</p>
          </article>
          <article class="lp-card">
            <div class="lp-card-icon">👁</div>
            <div class="lp-card-title">{{ t("landing.feature6Title") }}</div>
            <p class="lp-card-copy">{{ t("landing.feature6Copy") }}</p>
          </article>
        </div>
      </div>
    </section>

    <div class="lp-shell"><div class="lp-divider"></div></div>

    <!-- ═══════ HOW IT WORKS ═══════ -->
    <section id="how" class="lp-section fade-up">
      <div class="lp-shell">
        <div class="lp-label">{{ t("landing.howLabel") }}</div>
        <h2 class="lp-section-title">{{ t("landing.howTitle") }}</h2>
        <p class="lp-section-lead">{{ t("landing.howLead") }}</p>
        <div class="lp-how">
          <div>
            <div class="lp-step">
              <div class="lp-step-num">1</div>
              <div>
                <div class="lp-step-title">{{ t("landing.step1Title") }}</div>
                <p class="lp-step-copy">{{ t("landing.step1Copy") }}</p>
              </div>
            </div>
            <div class="lp-step">
              <div class="lp-step-num">2</div>
              <div>
                <div class="lp-step-title">{{ t("landing.step2Title") }}</div>
                <p class="lp-step-copy">{{ t("landing.step2Copy") }}</p>
              </div>
            </div>
            <div class="lp-step">
              <div class="lp-step-num">3</div>
              <div>
                <div class="lp-step-title">{{ t("landing.step3Title") }}</div>
                <p class="lp-step-copy">{{ t("landing.step3Copy") }}</p>
              </div>
            </div>
          </div>
          <div style="display:grid;gap:12px;">
            <div class="lp-role-card coach">
              <div class="lp-role-badge coach">Coach</div>
              <div class="lp-role-heading">{{ t("landing.forCoaches") }}</div>
              <ul class="lp-role-list">
                <li>{{ t("landing.coachBullet1") }}</li>
                <li>{{ t("landing.coachBullet2") }}</li>
                <li>{{ t("landing.coachBullet3") }}</li>
                <li>{{ t("landing.coachBullet4") }}</li>
              </ul>
            </div>
            <div class="lp-role-card athlete">
              <div class="lp-role-badge athlete">Athlete</div>
              <div class="lp-role-heading">{{ t("landing.forAthletes") }}</div>
              <ul class="lp-role-list">
                <li>{{ t("landing.athleteBullet1") }}</li>
                <li>{{ t("landing.athleteBullet2") }}</li>
                <li>{{ t("landing.athleteBullet3") }}</li>
                <li>{{ t("landing.athleteBullet4") }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="lp-shell"><div class="lp-divider"></div></div>

    <!-- ═══════ AUDIENCE ═══════ -->
    <section id="audience" class="lp-section fade-up">
      <div class="lp-shell">
        <div class="lp-label">{{ t("landing.audienceLabel") }}</div>
        <h2 class="lp-section-title">{{ t("landing.audienceTitle") }}</h2>
        <p class="lp-section-lead">{{ t("landing.audienceLead") }}</p>
        <div class="lp-grid-3">
          <article class="lp-audience-card">
            <div class="lp-audience-title">{{ t("landing.audience1Title") }}</div>
            <p class="lp-audience-copy">{{ t("landing.audience1Copy") }}</p>
          </article>
          <article class="lp-audience-card">
            <div class="lp-audience-title">{{ t("landing.audience2Title") }}</div>
            <p class="lp-audience-copy">{{ t("landing.audience2Copy") }}</p>
          </article>
          <article class="lp-audience-card">
            <div class="lp-audience-title">{{ t("landing.audience3Title") }}</div>
            <p class="lp-audience-copy">{{ t("landing.audience3Copy") }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- ═══════ CTA ═══════ -->
    <div class="lp-shell">
      <section class="lp-cta fade-up">
        <div class="lp-cta-heading">{{ t("landing.ctaHeading") }}</div>
        <p class="lp-cta-sub">{{ t("landing.ctaSub") }}</p>
        <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
          <a
            v-if="registrationEnabled"
            class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill"
            href="/accounts/signup/"
          >{{ t("landing.startFree") }}</a>
          <a
            v-else
            class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill eb-btn-disabled"
          >{{ t("landing.startFree") }}</a>
          <a class="lp-btn lp-btn-secondary lp-btn-lg" href="/accounts/login/">{{ t("landing.login") }}</a>
        </div>
      </section>
    </div>

  </main>
</template>

<script setup lang="ts">
definePageMeta({ layout: "public" })

const { t } = useI18n()

const registrationEnabled = true // Task 9 will add dynamic loading from API

useSeoMeta({
  title: t("landing.seoTitle"),
  description: t("landing.seoDescription"),
})

// Intersection Observer for fade-up animations
onMounted(() => {
  const elements = document.querySelectorAll(".fade-up")
  if (!elements.length) return
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return
        entry.target.classList.add("visible")
        observer.unobserve(entry.target)
      })
    },
    { threshold: 0.12 },
  )
  elements.forEach((el) => observer.observe(el))
})
</script>
