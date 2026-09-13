<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Third Party Services
    |--------------------------------------------------------------------------
    */

    'postmark' => [
        'key' => env(
            'POSTMARK_API_KEY'
        ),
    ],


    'resend' => [
        'key' => env(
            'RESEND_API_KEY'
        ),
    ],


    'ses' => [
        'key' => env(
            'AWS_ACCESS_KEY_ID'
        ),

        'secret' => env(
            'AWS_SECRET_ACCESS_KEY'
        ),

        'region' => env(
            'AWS_DEFAULT_REGION',
            'us-east-1'
        ),
    ],


    'slack' => [
        'notifications' => [

            'bot_user_oauth_token' =>
                env(
                    'SLACK_BOT_USER_OAUTH_TOKEN'
                ),

            'channel' =>
                env(
                    'SLACK_BOT_USER_DEFAULT_CHANNEL'
                ),
        ],
    ],


    /*
    |--------------------------------------------------------------------------
    | JWT
    |--------------------------------------------------------------------------
    */

    'jwt' => [

        'signing_key' => env(
            'JWT_SIGNING_KEY',
            ''
        ),

    ],


    /*
    |--------------------------------------------------------------------------
    | SERVICIO CLÍNICO
    |--------------------------------------------------------------------------
    |
    | NO utilizar:
    |
    | http://servicio_clinico:8000
    |
    | porque Django rechaza "_" dentro del HTTP Host.
    |
    | Se utiliza el alias válido creado en docker-compose:
    |
    | servicio-clinico
    |
    */

    'clinico' => [

        'base_url' => env(
            'CLINICO_SERVICE_BASE_URL',
            'http://servicio-clinico:8000/api'
        ),

    ],

];