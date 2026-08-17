# frozen_string_literal: true

# Jekyll plugin for generating multilingual pages with i18n support
module Jekyll
  # Extends Site to store locale translations
  class Site
    attr_accessor(:locales)
  end

  SCOPE_ORDER = {
    'phases' => 1,
    'tactics' => 2,
    'techniques' => 3,
    'mitigations' => 4,
    'detections' => 5,
    'tools' => 6,
    'notes' => 7,
    'contributors' => 8
  }.freeze
  private_constant :SCOPE_ORDER

  def self.translate(site, lang, message, fallback = nil)
    site.locales&.dig(lang || site.config['lang'], message) || fallback || message
  end

  # Generates multilingual pages from data files
  class LocalePagesGenerator < Generator
    safe true
    priority :high

    def generate(site)
      @exists_pages = get_exists_pages(site)
      generate_pages(site)
      # Ensure root index exists
      site.pages << LocaleIndexPage.new(site, nil) unless site.pages.any? { |page| page.dir == '/' && page.index? }
      NavigationBuilder.build(site)
    end

    private

    def get_exists_pages(site)
      old_pages, new_pages, exists_pages = collect_page_variants(site)
      site.pages.reject! { |page| old_pages.include?(page) }
      site.pages.concat(new_pages)
      exists_pages
    end

    def collect_page_variants(site)
      old_pages = []
      new_pages = []
      exists_pages = site.pages.each_with_object(Set.new) do |page, set|
        next if skip_page?(page)

        locale_pages = create_locale_variants(site, page)
        new_pages.concat(locale_pages)
        old_pages << page unless locale_pages.empty?
        set.add(page.index? ? page.dir : "#{page.dir}#{page.basename}#{page.output_ext}")
      end
      [old_pages, new_pages, exists_pages]
    end

    def skip_page?(page)
      page.is_a?(DataAsset) || page.url.start_with?('/assets')
    end

    def create_locale_variants(site, page)
      ([nil] + site.config['supported_languages']).map do |lang|
        LocalePageFromAPage.new(site, lang, page)
      end
    end

    def page_exists?(*parts)
      @exists_pages.include?("/#{parts.compact.join('/')}/".squeeze('/'))
    end

    def generate_pages(site)
      ([nil] + site.config['supported_languages']).each do |lang|
        next if lang && lang == site.config['lang']

        generate_index_pages(site, lang, site.data['pages'])
      end
    end

    def generate_index_pages(site, lang, data, *parts)
      return unless data.is_a?(Hash)

      site.pages << LocaleIndexPage.new(site, lang, data, *parts) unless page_exists?(*parts)
      generate_table_pages(site, lang, data, *parts)
    end

    def generate_table_pages(site, lang, data, *parts)
      data.each do |key, value|
        case value
        when Array
          active_records = generate_record_pages(site, lang, value, *parts, key)
          next if active_records.empty?

          site.pages << LocaleTablePage.new(site, lang, active_records, *parts, key) unless page_exists?(*parts, key)
        when Hash
          generate_index_pages(site, lang, value, key, *parts)
        end
      end
    end

    def generate_record_pages(site, lang, records, *parts)
      records.each_with_object([]) do |record, active_records|
        next unless record.is_a?(Hash) && record['id']

        site.pages << LocaleRecordPage.new(site, lang, record, *parts) unless page_exists?(*parts, record['id'])
        active_records << record unless record['revoked']
      end
    end
  end

  # Serves static files from _data directory without rendering
  class DataAsset < PageWithoutAFile
    def initialize(site, full_path, *parts)
      super(site, site.source, "/#{parts.compact.join('/')}", File.basename(full_path))
      @source_path = full_path
      @data['permalink'] = "#{@dir}/".squeeze('/') + @name
      @data['layout'] = nil
    end

    def content
      return '' unless write?

      @content ||= File.read(@source_path)
    end

    def write?
      File.exist?(@source_path)
    end
  end

  # Base page class with language prefix and redirect support
  class LocalePage < PageWithoutAFile
    def initialize(site, lang, *parts, name: 'index.html')
      @base_dir = "/#{parts.compact.reject(&:empty?).join('/')}/".squeeze('/')
      super(site, site.source, "/#{lang}#{@base_dir}".squeeze('/'), name)
      @lang = lang
      @data['permalink'] = index? ? @dir : "#{@dir}#{basename}#{output_ext}"
      @data['lang'] = @lang
      @data['base_dir'] = @base_dir
      redirect_from = hydrate_redirects
      @data['redirect_from'] = redirect_from unless redirect_from.nil?
    end

    private

    def hydrate_redirects
      lang = @lang || @site.config['lang']
      supported_languages = @site.config['supported_languages']
      return unless supported_languages&.include?(lang)

      paths = permalink_variants(lang)
      paths.empty? ? nil : paths
    end

    def permalink_variants(lang)
      suffix = permalink.sub(%r{^/#{Regexp.escape(lang)}}, '')
      supported_languages = @site.config['supported_languages']
      lang_variants(lang).filter_map do |variant|
        path = "/#{variant}#{suffix}"
        next if permalink == path || (lang != @site.config['lang'] && supported_languages.include?(variant))

        path
      end
    end

    def lang_variants(lang)
      return [] unless lang

      [
        lang,
        lang.tr('_', '-'),
        lang.tr('-', '_'),
        lang.split(/[-_]/).first
      ].uniq
    end
  end

  # Locale variant page based on original page with inherited path handling
  class LocalePageFromAPage < Page
    def initialize(site, lang, original_page)
      super(site, site.source, original_page.dir, original_page.name)
      @data.merge!(
        LocalePage.new(site, lang, @dir, name: @name).data.slice(
          'permalink', 'lang', 'base_dir', 'redirect_from'
        )
      )
    end
  end

  # Index page for a namespace or root directory
  class LocaleIndexPage < LocalePage
    def initialize(site, lang, source = nil, namespace = nil, *parts)
      super(site, lang, namespace, *parts)
      @data['layout'] = 'index'
      @data['title'] = namespace&.upcase || Jekyll.translate(@site, @lang, 'home').capitalize
      @data['source'] = source
    end
  end

  # Category listing page with filtered items
  class LocaleTablePage < LocalePage
    def initialize(site, lang, source, *parts, scope)
      super(site, lang, *parts, scope)
      @data['layout'] = 'table'
      @data['title'] = Jekyll.translate(@site, @lang, scope)&.capitalize
      @data['source'] = source
      @data['scope'] = scope
      @data['order'] = SCOPE_ORDER[scope]
    end
  end

  # Individual item detail page with localized title formatting
  class LocaleRecordPage < LocalePage
    def initialize(site, lang, source, *parts)
      @id = source['id']
      super(site, lang, *parts, name: "#{@id}.html")
      @data['layout'] = 'record'
      @data['title'] = source['name']&.to_s if %w[individual organization].include?(source['type'])
      @data['title'] ||= "#{Jekyll.translate(@site, @lang, source['type'])&.capitalize}: #{source['name']}"
      @data['source'] = source
    end
  end

  # Site initialization and setup utilities
  module Setup
    extend self

    def configure(site)
      load_locales(site)
      site.config['lang'] = site.config['lang'].then { strip_or_nil(_1) } || detect_language(site)
      site.config['supported_languages'] = get_supported_languages(site)
    end

    private

    def strip_or_nil(value)
      value&.to_s&.strip.then { _1&.empty? ? nil : _1 }
    end

    def load_locales(site)
      site.locales = site.data['locales'].is_a?(Hash) ? site.data['locales'] : {}
      Jekyll.logger.info 'Load Locales:', "Loaded #{site.locales.keys.size} locale(s): #{site.locales.keys.join(', ')}"
      # Release site.data['locales'] to save memory (data already copied to site.locales)
      site.data.delete('locales')
    end

    def detect_language(site)
      %w[LANGUAGE LC_ALL LC_MESSAGES LANG].each do |env_var|
        next unless (value = ENV[env_var])

        # Split by ':' to support multiple languages (e.g., "zh_TW:en")
        languages = value.split(':').map { _1.split('.').first.tr('_', '-') }
        if (found = languages.find { site.locales&.key?(_1) })
          Jekyll.logger.info 'Language:', "Using #{env_var}=#{found}"
          return found
        end
      end
      nil
    end

    def get_supported_languages(site)
      available_languages = site.locales&.keys || []
      supported_languages = site.config['supported_languages']
      return available_languages if supported_languages.nil?

      if supported_languages.is_a?(Hash)
        filter_native_names(site, supported_languages)
      else
        (supported_languages.is_a?(Array) ? supported_languages : [supported_languages]
        ).map(&:to_s) & available_languages
      end
    end

    def filter_native_names(site, languages)
      languages.select do |lang, name|
        next false if name == false

        site.locales[lang] ||= {}
        site.locales[lang]['_native_name'] = name if (name = strip_or_nil(name))
        true
      end.keys
    end
  end

  # Processes data by sanitizing and building hierarchical relationships
  module DataProcessor # rubocop:disable Metrics/ModuleLength
    extend self

    ASSET_HANDLERS = {
      ENV.fetch('FIST_ARTIFACT', 'bundle.json') => lambda { |data, basename|
        data['version'] ||= data&.dig(basename, 'objects')&.filter_map { _1['x_fist_version'] }&.first
        data.delete(basename)
      }
    }.freeze
    private_constant :ASSET_HANDLERS

    def process(site)
      data = site.data['pages']
      sanitize_assets(data, site, 'pages')
      sanitize_buckets(data)
      sanitize_scopes(data)
    end

    private

    def sanitize_assets(data, site, *parts)
      return unless data.is_a?(Hash)

      ASSET_HANDLERS.each do |filename, handler|
        full_path = File.join(site.source, '_data', *parts, filename)
        next unless File.exist?(full_path)

        site.pages << DataAsset.new(site, full_path, *parts[1..])
        handler.call(data, File.basename(full_path, '.*'))
      end
      data.each { sanitize_assets(_2, site, *parts, _1) }
    end

    def sanitize_buckets(data, visited = Set.new)
      return unless data.is_a?(Hash)
      return if visited.include?(data.object_id)

      visited.add(data.object_id)
      data.each do |key, value|
        data[key] = value.values if table?(value)
        value.each { sanitize_buckets(_1, visited) } if value.is_a?(Array)
        sanitize_buckets(value, visited)
      end
    end

    def table?(data)
      data.is_a?(Hash) && data.values.all? { _1.is_a?(Hash) && _1['id'] }
    end

    def sanitize_scopes(data)
      return unless data.is_a?(Hash)

      if (data.keys & SCOPE_ORDER.keys).any?
        scopes = SCOPE_ORDER.each_key.to_h { [_1, data[_1] || []] }
        hydrate_scopes(scopes, lookups(scopes))
        data.merge!(scopes.except(*SCOPE_ORDER.keys))
      end

      data.each_value { sanitize_scopes(_1) }
    end

    def lookups(data)
      data.keys.to_h do |scope|
        records = data[scope]&.reject { _1['revoked'] }&.to_h do |record|
          lookup = record.slice('id', 'name', 'description')
          lookup.merge!(embed_ids(record)) if scope == 'techniques'
          [record['id'], lookup]
        end
        [scope, records || {}]
      end
    end

    def embed_ids(record)
      {
        'tool_ids' => record['tools']&.filter_map { _1['id'] } || [],
        'mitigation_ids' => record['mitigations']&.filter_map { _1['id'] } || [],
        'detection_ids' => record.dig('detection', 'components')&.filter_map { _1['id'] } || []
      }
    end

    def hydrate_scopes(data, lookups)
      hydrate_phases(data)
      hydrate_tactics(data, lookups)
      hydrate_techniques(data, lookups)
      hydrate_mitigations(data, lookups)
      hydrate_detections(data, lookups)
      hydrate_tools(data, lookups)
      hydrate_notes(data, lookups)
      hydrate_contributors(data)
      data['max_techniques_index'] = data['tactics']&.map { _1['techniques']&.size }&.max&.-(1) || 0
    end

    def hydrate_phases(data)
      tactics_by_phase = data['tactics'].reject { _1['revoked'] }.group_by { _1['phase_id'] }
      data['phases'].each do |phase|
        phase['tactics'] = tactics_by_phase[phase['id']] || []
      end
    end

    def hydrate_tactics(data, lookups)
      techniques_by_tactic = data['techniques'].reject { _1['revoked'] || _1['parent_id'] }.group_by { _1['tactic_id'] }
      data['tactics'].each do |tactic|
        tactic['phase'] = lookups['phases'][tactic['phase_id']]
        tactic['techniques'] = techniques_by_tactic[tactic['id']] || []
      end
    end

    def hydrate_techniques(data, lookups) # rubocop:disable Metrics/AbcSize
      sub_techniques_by_parent = data['techniques'].reject { _1['revoked'] }.group_by { _1['parent_id'] }
      data['techniques'].each do |technique|
        technique['tactic'] = lookups['tactics'][technique['tactic_id']]
        technique['parent'] = lookups['techniques'][technique['parent_id']]
        technique['sub_techniques'] = sub_techniques_by_parent[technique['id']] || []
        technique['mitigations'].each { _1.merge!(lookups['mitigations'][_1['id']]) { |_, old, _| old } }
        technique['tools'].each { _1.merge!(lookups['tools'][_1['id']]) { |_, old, _| old } }
        technique['detection']['components'].each { _1.merge!(lookups['detections'][_1['id']]) { |_, old, _| old } }
      end
    end

    def hydrate_mitigations(data, lookups)
      techniques_by_mitigation = lookups['techniques'].flat_map { |_, e| e['mitigation_ids'].map { [_1, e] } }
                                                      .group_by(&:first).transform_values { _1.map(&:last) }
      data['mitigations'].each do |mitigation|
        mitigation['related'] = { 'techniques' => techniques_by_mitigation[mitigation['id']]
                                                  &.sort_by { _1['id'] } || [] }
      end
    end

    def hydrate_detections(data, lookups) # rubocop:disable Metrics/AbcSize
      components_by_parent = data['detections'].group_by { _1['parent_id'] }
      techniques_by_detection = lookups['techniques'].flat_map { |_, e| e['detection_ids'].map { [_1, e] } }
                                                     .group_by(&:first).transform_values { _1.map(&:last) }
      data['detections'].each do |detection|
        detection['source'] = lookups['detections'][detection['parent_id']]
        detection['components'] = components_by_parent[detection['id']] || []
        detection['related'] = { 'techniques' => [detection, *detection['components']]
                                                 .flat_map { techniques_by_detection[_1['id']] || [] }
                                                 .uniq.sort_by { _1['id'] } }
      end
    end

    def hydrate_tools(data, lookups)
      techniques_by_tool = lookups['techniques'].flat_map { |_, e| e['tool_ids'].map { [_1, e] } }
                                                .group_by(&:first).transform_values { _1.map(&:last) }
      data['tools'].each do |tool|
        tool['related'] = { 'techniques' => techniques_by_tool[tool['id']]
                                            &.sort_by { _1['id'] } || [] }
      end
    end

    def hydrate_notes(data, lookups)
      data['notes'].each do |note|
        note['related'] = lookups.except('notes', 'contributors').transform_values do |lookup|
          note['related_ids']&.filter_map { lookup[_1] }&.sort_by { _1['id'] } || []
        end
      end
    end

    def hydrate_contributors(data)
      data['contributors'].each do |contributor|
        contributor['headshot'] ||= "https://ui-avatars.com/api/?name=#{CGI.escape(contributor['id']&.to_s)}&size=128"
      end
    end
  end

  # Builds navigation data for all pages based on index pages
  module NavigationBuilder
    extend self

    def build(site)
      groups = get_navigation_groups(site.pages)
      site.pages.each do |page|
        next unless page.respond_to?(:url)

        page.data['navigation'] = get_navigation_pages(groups[page.data['lang']], path_segments(page))
      end
    end

    private

    def get_navigation_groups(pages)
      groups = Hash.new { |h, k| h[k] = { root: [], children: {} } }
      pages.each do |page|
        next unless navigation_page?(page)

        add_to_navigation_group(groups[page.data['lang']], path_segments(page), page)
      end
      groups
    end

    def navigation_page?(page)
      page.respond_to?(:url) && page.respond_to?(:name) && page.index? && page.data['title']
    end

    def path_segments(page)
      lang = page.data['lang']
      parts = page.dir.split('/').reject(&:empty?)
      parts.shift if lang && parts.first == lang
      parts
    end

    def add_to_navigation_group(group, parts, page)
      case parts.size
      when 1
        group[:root] << page
      when 2
        namespace = parts.first
        group[:children][namespace] ||= []
        group[:children][namespace] << page
      end
    end

    def get_navigation_pages(group, segments)
      return [] unless group

      pages = (segments.empty? ? group[:root] : (group[:children][segments.first] || group[:root])).map do |page|
        {
          'title' => page.data['title'],
          'url' => page.url,
          'order' => page.data['order'] || 0
        }
      end
      pages.sort_by { |page| page['order'] }
    end
  end

  # Provides filters for URL localization and text transformation
  module I18nFilters
    def localize(url, lang = nil)
      page = @context.registers[:page]
      site = @context.registers[:site]
      url ||= page['url'].sub(%r{^/#{"#{page['lang']}/" if page['lang']}}, '/')
      return url unless url&.start_with?('/')

      [site.config['baseurl'], lang || page['lang'], url[1..]].compact.join('/')
    end

    def smart_join(input, separator = nil, raw = false) # rubocop:disable Metrics/CyclomaticComplexity,Style/OptionalBooleanParameter
      site = @context.registers[:site]
      page = @context.registers[:page]
      lang = page['lang'] || site.config['lang']
      input&.map { raw ? _1 : titleize(translate(_1, _1)) }&.join(
        (separator.is_a?(Hash) ? separator[lang] : separator&.to_s) || translate('_separator', ' ')
      )
    end

    def titleize(input)
      input&.to_s&.split&.map(&:capitalize)&.join(' ')
    end

    def translate(input, fallback = nil, lang = nil)
      site = @context.registers[:site]
      page = @context.registers[:page]
      Jekyll.translate(site, lang || page['lang'], input, fallback)
    end

    def reliability_grade(input)
      return nil if input.nil? || input.to_s.empty?

      translate("_reliability_#{input.to_s.upcase}", input.to_s.upcase)
    end
  end
end

Jekyll::Hooks.register :site, :post_read do |site|
  Jekyll::Setup.configure(site)
  Jekyll::DataProcessor.process(site)
end

Liquid::Template.register_filter(Jekyll::I18nFilters)
