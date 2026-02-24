<?php
/**
 * Nature Positive Roadmap Theme functions and definitions.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Theme setup.
 */
function nature_roadmap_setup() {
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'html5', array( 'search-form', 'comment-form', 'gallery', 'caption', 'style', 'script' ) );
}
add_action( 'after_setup_theme', 'nature_roadmap_setup' );

/**
 * Enqueue scripts and styles.
 */
function nature_roadmap_scripts() {
    // Google Fonts
    wp_enqueue_style(
        'nature-roadmap-google-fonts',
        'https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500;600;700;900&family=Roboto+Condensed:wght@400;500;600;700&display=swap',
        array(),
        null
    );

    // Theme stylesheet
    wp_enqueue_style(
        'nature-roadmap-style',
        get_stylesheet_uri(),
        array( 'nature-roadmap-google-fonts' ),
        wp_get_theme()->get( 'Version' )
    );

    // JavaScript
    wp_enqueue_script(
        'nature-roadmap-main',
        get_template_directory_uri() . '/js/main.js',
        array(),
        wp_get_theme()->get( 'Version' ),
        true
    );

    wp_enqueue_script(
        'nature-roadmap-roadmap',
        get_template_directory_uri() . '/js/roadmap.js',
        array(),
        wp_get_theme()->get( 'Version' ),
        true
    );

    wp_enqueue_script(
        'nature-roadmap-action-network',
        get_template_directory_uri() . '/js/action-network.js',
        array(),
        wp_get_theme()->get( 'Version' ),
        true
    );

    // Pass the theme directory URI to JavaScript for asset paths
    wp_localize_script( 'nature-roadmap-main', 'natureRoadmap', array(
        'themeUrl' => get_template_directory_uri(),
        'pdfUrl'   => get_template_directory_uri() . '/assets/Nature Positive Roadmap for New Developments.pdf',
    ) );
}
add_action( 'wp_enqueue_scripts', 'nature_roadmap_scripts' );
