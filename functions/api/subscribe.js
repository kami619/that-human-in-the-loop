export async function onRequestPost(context) {
  const { request, env } = context;
  const { email } = await request.json();

  if (!email || !email.includes('@')) {
    return new Response("Invalid Human", { status: 400 });
  }

  // 'WAITLIST' must be bound in the Cloudflare Dashboard under 'Functions'
  await env.WAITLIST.put(email, new Date().toISOString());

  return new Response(JSON.stringify({ status: "In the Loop" }), {
    headers: { "Content-Type": "application/json" }
  });
}
