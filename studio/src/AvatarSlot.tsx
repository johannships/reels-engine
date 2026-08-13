import React from 'react';
import {staticFile, Video} from 'remotion';
import {COLORS, FONTS, LAYOUT} from './theme';

/**
 * Bottom half of the frame (1080x960). When `avatarSrc` is provided it is
 * scaled to cover the slot and cropped around `focusY` (a 0-1 fraction of the
 * source height, so a portrait selfie can keep the face centered). Works with
 * landscape (1920x1080) and portrait (1080x1920) sources alike. Without a
 * source it renders a labeled placeholder so the template previews cleanly.
 */
export const AvatarSlot: React.FC<{
  avatarSrc?: string;
  sourceW?: number;
  sourceH?: number;
  focusY?: number;
  /**
   * Render the slot fully transparent (except the seam border) so the avatar
   * video can be composited under this layer by ffmpeg. This avoids playing
   * video inside the browser during renders, which is the one unreliable part
   * of headless Chrome.
   */
  transparent?: boolean;
}> = ({
  avatarSrc,
  sourceW = 1920,
  sourceH = 1080,
  focusY = 0.5,
  transparent = false,
}) => {
  const slotW = LAYOUT.width; // 1080
  const slotH = LAYOUT.avatarHeight; // 960

  // Cover the slot, then position so the focus point sits at slot center.
  const scale = Math.max(slotW / sourceW, slotH / sourceH);
  const renderW = sourceW * scale;
  const renderH = sourceH * scale;
  const maxOffsetY = renderH - slotH;
  const offsetY = Math.min(
    Math.max(focusY * renderH - slotH / 2, 0),
    Math.max(maxOffsetY, 0),
  );
  const offsetX = Math.max((renderW - slotW) / 2, 0);

  const resolvedSrc =
    avatarSrc && !/^(https?:|data:)/.test(avatarSrc)
      ? staticFile(avatarSrc)
      : avatarSrc;

  if (transparent) {
    return (
      <div
        style={{
          position: 'absolute',
          top: LAYOUT.avatarTop,
          left: 0,
          width: slotW,
          height: 2,
          background: COLORS.violet,
        }}
      />
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        top: LAYOUT.avatarTop,
        left: 0,
        width: slotW,
        height: slotH,
        background: COLORS.ground,
        overflow: 'hidden',
        borderTop: `2px solid ${COLORS.violet}`,
      }}
    >
      {resolvedSrc ? (
        <Video pauseWhenBuffering={false}
          src={resolvedSrc}
          style={{
            position: 'absolute',
            top: -offsetY,
            left: -offsetX,
            width: renderW,
            height: renderH,
          }}
        />
      ) : (
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span
            style={{
              fontFamily: FONTS.body,
              fontWeight: 600,
              fontSize: 34,
              letterSpacing: '0.35em',
              color: 'rgba(164, 159, 179, 0.28)',
            }}
          >
            HEYGEN AVATAR
          </span>
        </div>
      )}
    </div>
  );
};
