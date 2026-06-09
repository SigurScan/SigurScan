FROM mcr.microsoft.com/playwright:v1.56.1-noble

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --omit=dev

COPY src ./src
COPY samples ./samples
COPY docs ./docs
COPY supabase ./supabase
COPY README.md ./README.md
COPY .env.example ./.env.example

RUN mkdir -p /app/output && chown -R pwuser:pwuser /app
USER pwuser

ENTRYPOINT ["node", "src/index.js"]
CMD ["--email-source", "./samples/official_preview_targets.ro.json", "--out-dir", "./output", "--concurrency", "1"]
