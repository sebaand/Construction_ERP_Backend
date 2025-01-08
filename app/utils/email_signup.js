

exports.onExecutePostUserRegistration = async (event, api) => {
  // You can use any email service like SendGrid, AWS SES, or NodeMailer
  // Here's an example using NodeMailer
  const nodemailer = require('nodemailer');

  const transporter = nodemailer.createTransport({
    service: 'gmail',  // or your preferred email service
    auth: {
      user: 'sitesteer.ai@gmail.com',
      pass: 'yomf ugad ixsl zldd'
    }
  });

  const mailOptions = {
    from: 'sitesteer.ai@gmail.com',
    to: 'andreasebastio014@gmail.com',
    subject: 'New User Registration',
    text: `New user registered:
    Email: ${event.user.email}
    Name: ${event.user.user_metadata.name || 'Not provided'}
    Organization: ${event.user.user_metadata.organization || 'Not provided'}
    Marketing Status: ${event.user.user_metadata.marketing_accepted ? 'Accepted' : 'Not accepted'}
    Time: ${new Date().toISOString()}`
  };

  try {
    await transporter.sendMail(mailOptions);
  } catch (error) {
    console.error('Failed to send email:', error);
  }
};