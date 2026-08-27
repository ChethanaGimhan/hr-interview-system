# Stage 1: dependencies
FROM node:22-alpine AS deps
WORKDIR /app
# Only the two files that describe the dependencies, so this layer is rebuilt
# when a package changes but not when application code changes.
COPY package.json package-lock.json ./
# npm ci installs exactly what the lock file says. npm install is allowed to
# resolve a newer version, which would make two builds of the same commit
# produce different images.
RUN npm ci

# Stage 2: build
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: the image that actually runs
FROM node:22-alpine
# Patch whatever the base image shipped with, the same idea as apt-get upgrade
# in the backend image.
RUN apk upgrade --no-cache
# npm and corepack are only needed to install and to build, and both of those
# happened in earlier stages that get thrown away. Trivy found 9 fixable
# CRITICAL and HIGH issues in the packages npm bundles - tar, sigstore,
# picomatch and others - and this image never runs any of them. Deleting them
# takes that count to 0 and leaves nothing here that can install more code.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup -S nodejs && adduser -S nextjs -G nodejs

# output: standalone put everything the app needs into these two folders, so
# node_modules never has to be copied here at all.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
# 0.0.0.0 rather than the default, otherwise the server only listens inside the
# container and the published port reaches nothing.
ENV PORT=3000 HOSTNAME=0.0.0.0
CMD ["node", "server.js"]
