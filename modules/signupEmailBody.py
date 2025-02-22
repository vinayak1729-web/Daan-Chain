def Sign_up_email_body_template(username, otp):
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email Verification - Surya Prabha</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #0056b3;
            margin-top: 0;
        }}
        p {{
            margin-bottom: 15px;
        }}
        .otp-code {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
            background-color: #e9ecef;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 14px;
            color: #777;
        }}
        .team-name {{
            font-weight: bold;
            color: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Verify Your Email Address</h2>
        <p>Dear {username},</p>
        <p>Thank you for signing up with Surya Prabha! To complete your registration and activate your account, please verify your email address using the One-Time Password (OTP) below.</p>
        <p>This OTP is valid for a short period for security reasons. Please enter it on the verification page to proceed.</p>

        <div class="otp-code">
            {otp}
        </div>

        <p>If you did not sign up for Surya Prabha, please ignore this email. No further action is required.</p>

        <div class="footer">
            <p>Thank you,</p>
            <p class="team-name">Team Surya Prabha</p>
            <p><small>If you have any questions, please contact our support team.</small></p>
        </div>
    </div>
</body>
</html>
"""